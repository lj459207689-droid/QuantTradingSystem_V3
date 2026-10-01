# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pytest

from quant_system.risk.drawdown import (
    drawdown_series,
    max_drawdown,
    current_drawdown,
    drawdown_duration,
    DrawdownController,
    PositionStopLoss,
    PositionState,
)


class TestDrawdownSeries:
    def test_known_max_drawdown(self, equity_with_drawdown):
        """fixture 手工构造的回撤恰好是 20%。"""
        result = max_drawdown(equity_with_drawdown)
        assert result == pytest.approx(0.20, abs=1e-6)

    def test_no_drawdown_on_monotonic_rise(self, rising_equity):
        assert max_drawdown(rising_equity) == pytest.approx(0.0)
        assert (drawdown_series(rising_equity) == 0.0).all()

    def test_rejects_non_series(self):
        with pytest.raises(TypeError):
            drawdown_series([1, 2, 3])

    def test_rejects_nan(self, dates):
        s = pd.Series([100.0, np.nan, 90.0], index=dates[:3])
        with pytest.raises(ValueError):
            drawdown_series(s)

    def test_rejects_non_positive_equity(self, dates):
        s = pd.Series([100.0, 0.0, 90.0], index=dates[:3])
        with pytest.raises(ValueError):
            drawdown_series(s)

    def test_current_drawdown_is_last_value(self, equity_with_drawdown):
        dd = drawdown_series(equity_with_drawdown)
        assert current_drawdown(equity_with_drawdown) == pytest.approx(dd.iloc[-1])

    def test_empty_series(self, dates):
        empty = pd.Series(dtype=float)
        assert max_drawdown(empty) == 0.0
        assert current_drawdown(empty) == 0.0


class TestDrawdownDuration:
    def test_counts_consecutive_periods(self, dates):
        # 100 -> 90(回撤) -> 85(回撤延续) -> 100(创新高,回撤清零) -> 95(回撤重新计数)
        values = [100, 90, 85, 100, 95]
        s = pd.Series(values, index=dates[:5])
        duration = drawdown_duration(s)
        assert duration.tolist() == [0, 1, 2, 0, 1]


class TestDrawdownController:
    def test_default_thresholds_sorted(self):
        ctrl = DrawdownController()
        thresholds = [t for t, _ in ctrl.thresholds]
        assert thresholds == sorted(thresholds)

    def test_scale_below_first_threshold_is_full_position(self):
        ctrl = DrawdownController([(0.10, 0.6), (0.20, 0.0)])
        assert ctrl.scale_for_drawdown(0.05) == 1.0

    def test_scale_exactly_at_threshold_triggers_that_tier(self):
        """边界情况：回撤恰好等于阈值时应该已经触发该档位（>=判断）。"""
        ctrl = DrawdownController([(0.10, 0.6), (0.20, 0.0)])
        assert ctrl.scale_for_drawdown(0.10) == 0.6

    def test_scale_beyond_last_threshold(self):
        ctrl = DrawdownController([(0.10, 0.6), (0.20, 0.0)])
        assert ctrl.scale_for_drawdown(0.30) == 0.0

    def test_invalid_drawdown_range_raises(self):
        ctrl = DrawdownController()
        with pytest.raises(ValueError):
            ctrl.scale_for_drawdown(1.5)
        with pytest.raises(ValueError):
            ctrl.scale_for_drawdown(-0.1)

    def test_invalid_threshold_construction_raises(self):
        with pytest.raises(ValueError):
            DrawdownController([(1.5, 0.5)])  # threshold 超出 [0,1]
        with pytest.raises(ValueError):
            DrawdownController([(0.1, 1.5)])  # scale 超出 [0,1]

    def test_apply_current_uses_only_past_peak(self):
        """
        实盘接口 apply_current：如果 current_equity 超过 peak_equity，
        应该把 peak 更新为 current(回撤=0)，而不是用旧的 peak 算出负回撤。
        """
        ctrl = DrawdownController([(0.10, 0.5)])
        result = ctrl.apply_current(
            target_position=1.0, current_equity=1_100_000, peak_equity=1_000_000
        )
        assert result == 1.0  # 创新高，无缩减

    def test_apply_current_rejects_non_positive(self):
        ctrl = DrawdownController()
        with pytest.raises(ValueError):
            ctrl.apply_current(target_position=1.0, current_equity=0, peak_equity=100)

    def test_apply_series_aligns_and_scales(self, dates):
        ctrl = DrawdownController([(0.10, 0.5), (0.20, 0.0)])
        equity = pd.Series([100, 90, 80, 100], index=dates[:4])  # dd: 0, 0.1, 0.2, 0
        position = pd.Series([1.0, 1.0, 1.0, 1.0], index=dates[:4])
        result = ctrl.apply(position, equity)
        assert result.tolist() == pytest.approx([1.0, 0.5, 0.0, 1.0])

    def test_apply_rejects_non_series_position(self, equity_with_drawdown):
        ctrl = DrawdownController()
        with pytest.raises(TypeError):
            ctrl.apply([1, 2, 3], equity_with_drawdown)


class TestPositionStopLoss:
    def test_invalid_construction(self):
        with pytest.raises(ValueError):
            PositionStopLoss(stop_loss_pct=0)
        with pytest.raises(ValueError):
            PositionStopLoss(stop_loss_pct=1.5)
        with pytest.raises(ValueError):
            PositionStopLoss(cooldown_days=-1)

    def test_long_position_stop_triggers_at_threshold(self):
        sl = PositionStopLoss(stop_loss_pct=0.08)
        # 多头，成本100，跌破92(跌8%)应触发
        assert sl.check(quantity=100, average_price=100.0, current_price=91.9) is True
        assert sl.check(quantity=100, average_price=100.0, current_price=93.0) is False

    def test_short_position_stop_triggers_on_price_rise(self):
        sl = PositionStopLoss(stop_loss_pct=0.08)
        # 空头，成本100，涨破108(涨8%)应触发
        assert sl.check(quantity=-100, average_price=100.0, current_price=108.5) is True
        assert sl.check(quantity=-100, average_price=100.0, current_price=105.0) is False

    def test_no_position_never_triggers(self):
        sl = PositionStopLoss()
        assert sl.check(quantity=0, average_price=None, current_price=50.0) is False

    def test_invalid_price_raises(self):
        sl = PositionStopLoss()
        with pytest.raises(ValueError):
            sl.check(quantity=10, average_price=100, current_price=-1)

    def test_update_position_adds_weighted_average_cost(self):
        """
        同方向加仓：加权平均成本应正确计算。
        原100股@10元，再买100股@20元 -> 均价应为15元。
        """
        sl = PositionStopLoss()
        state = PositionState(quantity=100, average_price=10.0)
        new_state = sl.update_position(state, target_quantity=200, execution_price=20.0)
        assert new_state.average_price == pytest.approx(15.0)
        assert new_state.quantity == 200

    def test_update_position_reducing_keeps_original_cost(self):
        """同方向减仓：平均成本不应该变化（只有加仓才摊薄成本）。"""
        sl = PositionStopLoss()
        state = PositionState(quantity=200, average_price=15.0)
        new_state = sl.update_position(state, target_quantity=100, execution_price=30.0)
        assert new_state.average_price == pytest.approx(15.0)

    def test_update_position_reversal_resets_cost(self):
        """反向开仓（多翻空）：应该用新成交价作为新的平均成本。"""
        sl = PositionStopLoss()
        state = PositionState(quantity=100, average_price=10.0)
        new_state = sl.update_position(state, target_quantity=-50, execution_price=12.0)
        assert new_state.quantity == -50
        assert new_state.average_price == pytest.approx(12.0)

    def test_update_position_closing_clears_cost(self):
        sl = PositionStopLoss()
        state = PositionState(quantity=100, average_price=10.0)
        new_state = sl.update_position(state, target_quantity=0, execution_price=11.0)
        assert new_state.quantity == 0.0
        assert new_state.average_price is None

    def test_apply_series_triggers_cooldown(self, dates):
        """
        回测接口：价格跌破止损后应该清零持仓并进入冷却期，
        冷却期内即便 position 信号要求重新建仓也应保持0。
        """
        sl = PositionStopLoss(stop_loss_pct=0.08, cooldown_days=2)
        idx = dates[:6]
        # 100买入, 价格跌到90(跌10%,触发止损), 之后信号想重新买入也要等冷却期
        position = pd.Series([100, 100, 100, 100, 100, 100], index=idx)
        price = pd.Series([100, 100, 90, 95, 95, 95], index=idx)
        result = sl.apply(position, price)
        assert result.iloc[2] == 0  # 触发止损当期清仓
        assert result.iloc[3] == 0  # 冷却期第1天
        assert result.iloc[4] == 0  # 冷却期第2天
        assert result.iloc[5] == 100  # 冷却期结束，恢复信号持仓

    def test_apply_rejects_invalid_price(self, dates):
        sl = PositionStopLoss()
        position = pd.Series([100, 100], index=dates[:2])
        price = pd.Series([100, -1], index=dates[:2])
        with pytest.raises(ValueError):
            sl.apply(position, price)
