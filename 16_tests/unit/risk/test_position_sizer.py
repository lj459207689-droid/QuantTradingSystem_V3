# -*- coding: utf-8 -*-
import pytest

from quant_system.risk.position_sizer import (
    PositionSizer,
    RiskBudgetSizer,
    RiskParitySizer,
)


class TestPositionSizerConstruction:
    def test_invalid_risk_per_trade_raises(self):
        with pytest.raises(ValueError):
            PositionSizer(risk_per_trade=0)
        with pytest.raises(ValueError):
            PositionSizer(risk_per_trade=1.5)

    def test_invalid_max_position_weight_raises(self):
        with pytest.raises(ValueError):
            PositionSizer(max_position_weight=0)
        with pytest.raises(ValueError):
            PositionSizer(max_position_weight=1.5)

    def test_invalid_max_position_value_raises(self):
        with pytest.raises(ValueError):
            PositionSizer(max_position_value=-100)


class TestSizeByStop:
    def test_basic_calculation(self):
        """
        equity=100万, risk_per_trade=1% -> 风险预算=1万
        entry=100, stop=95 -> stop_distance=5
        quantity = 10000 / 5 = 2000 股(在max_position_weight限制内的话)
        """
        sizer = PositionSizer(risk_per_trade=0.01, max_position_weight=0.5, allow_fractional=True)
        result = sizer.size_by_stop(equity=1_000_000, entry_price=100, stop_price=95)
        assert result.quantity == pytest.approx(2000)
        assert result.risk_amount == pytest.approx(10_000)
        assert result.limited is False

    def test_zero_stop_distance_raises(self):
        sizer = PositionSizer()
        with pytest.raises(ValueError):
            sizer.size_by_stop(equity=1_000_000, entry_price=100, stop_price=100)

    def test_short_direction_returns_negative_quantity(self):
        sizer = PositionSizer(risk_per_trade=0.01, allow_fractional=True)
        result = sizer.size_by_stop(
            equity=1_000_000, entry_price=100, stop_price=105, direction=-1
        )
        assert result.quantity < 0

    def test_max_position_weight_limits_quantity(self):
        """
        风险预算算出的数量会超过最大仓位限制时，应该被裁剪，
        且 limited=True，reasons 中要说明原因。
        """
        sizer = PositionSizer(
            risk_per_trade=0.50,  # 故意设很大的风险预算，触发仓位上限
            max_position_weight=0.10,
            allow_fractional=True,
        )
        result = sizer.size_by_stop(equity=1_000_000, entry_price=100, stop_price=99)
        max_allowed = 1_000_000 * 0.10 / 100  # = 1000股
        assert result.quantity == pytest.approx(max_allowed)
        assert result.limited is True
        assert "最大仓位限制" in "".join(result.reasons)

    def test_lot_size_rounding(self):
        """lot_size=100 时数量应向下取整到100的倍数。"""
        sizer = PositionSizer(
            risk_per_trade=0.01, max_position_weight=0.5, lot_size=100, allow_fractional=False
        )
        result = sizer.size_by_stop(equity=1_000_000, entry_price=100, stop_price=97)
        # raw = 10000/3 = 3333.33 -> floor到100的倍数 = 3300
        assert result.quantity % 100 == 0
        assert result.limited is True

    def test_invalid_equity_raises(self):
        sizer = PositionSizer()
        with pytest.raises(ValueError):
            sizer.size_by_stop(equity=-1, entry_price=100, stop_price=95)

    def test_invalid_entry_price_raises(self):
        sizer = PositionSizer()
        with pytest.raises(ValueError):
            sizer.size_by_stop(equity=1_000_000, entry_price=0, stop_price=95)


class TestSizeByValue:
    def test_target_weight(self):
        sizer = PositionSizer(max_position_weight=0.5, allow_fractional=True)
        result = sizer.size_by_value(equity=1_000_000, price=50, target_weight=0.2)
        assert result.quantity == pytest.approx(4000)  # 20万/50元

    def test_missing_both_weight_and_value_raises(self):
        sizer = PositionSizer()
        with pytest.raises(ValueError):
            sizer.size_by_value(equity=1_000_000, price=50)

    def test_invalid_weight_range_raises(self):
        sizer = PositionSizer()
        with pytest.raises(ValueError):
            sizer.size_by_value(equity=1_000_000, price=50, target_weight=1.5)

    def test_target_weight_exceeding_max_is_clipped(self):
        sizer = PositionSizer(max_position_weight=0.1, allow_fractional=True)
        result = sizer.size_by_value(equity=1_000_000, price=50, target_weight=0.5)
        assert result.position_value == pytest.approx(100_000)  # 被裁到10%上限
        assert result.limited is True


class TestRiskBudgetSizer:
    def test_explicit_risk_budget_overrides_default(self):
        sizer = RiskBudgetSizer(max_position_weight=0.5, allow_fractional=True)
        qty = sizer.calculate(
            equity=1_000_000, entry_price=100, stop_price=95, risk_budget=20_000
        )
        assert qty == pytest.approx(4000)  # 20000/5

    def test_fallback_to_base_sizer_when_no_budget_given(self):
        sizer = RiskBudgetSizer(risk_per_trade=0.01, max_position_weight=0.5, allow_fractional=True)
        qty = sizer.calculate(equity=1_000_000, entry_price=100, stop_price=95)
        assert qty == pytest.approx(2000)


class TestRiskParitySizer:
    def test_higher_volatility_reduces_allocation(self):
        """
        target_risk 必须设置得足够小，否则两种波动率算出的目标金额
        都会被 max_position_weight 的上限裁剪到同一个值，掩盖波动率的影响。
        """
        sizer = RiskParitySizer(max_position_weight=1.0, allow_fractional=True)
        low_vol_qty = sizer.calculate(
            equity=1_000_000, price=100, volatility=0.1, target_risk=0.05
        )
        high_vol_qty = sizer.calculate(
            equity=1_000_000, price=100, volatility=0.4, target_risk=0.05
        )
        assert high_vol_qty < low_vol_qty

    def test_invalid_volatility_raises(self):
        sizer = RiskParitySizer()
        with pytest.raises(ValueError):
            sizer.calculate(equity=1_000_000, price=100, volatility=0)
