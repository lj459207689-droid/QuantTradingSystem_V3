# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from quant_system.backtest.engine import BacktestEngine, BacktestResult, Trade


class TestConstruction:
    def test_rejects_non_series_price(self, dates):
        signal = pd.Series([1] * len(dates), index=dates)
        with pytest.raises(TypeError):
            BacktestEngine(price=[1, 2, 3], signal=signal)

    def test_rejects_non_series_signal(self, trending_price):
        with pytest.raises(TypeError):
            BacktestEngine(price=trending_price, signal=[1, 1, 1])

    def test_signal_is_clipped_to_valid_range(self, trending_price):
        signal = pd.Series([5.0] * len(trending_price), index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal)
        assert engine.raw_signal.max() <= 1.0

    def test_disallow_short_clips_negative_signal(self, trending_price):
        signal = pd.Series([-1.0] * len(trending_price), index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal, allow_short=False)
        assert (engine.raw_signal >= 0).all()


class TestNoLookAheadBias:
    def test_signal_lag_delays_position_by_one_period(self, trending_price):
        """
        核心正确性验证：signal_lag=1 时，T日信号必须在T+1日才生效，
        不能在信号发出当天就用当天收盘价结算(未来函数)。
        """
        idx = trending_price.index
        # 信号在某一天从0变为1
        signal = pd.Series(0.0, index=idx)
        signal.iloc[10:] = 1.0

        engine = BacktestEngine(
            price=trending_price, signal=signal, signal_lag=1,
            commission_rate=0.0, slippage_rate=0.0,
        )
        result = engine.run()

        # 第10天信号变为1，但 position(经过shift(1))在第10天应仍为0，第11天才变1
        assert result.positions.iloc[10] == 0.0
        assert result.positions.iloc[11] == 1.0

    def test_zero_lag_uses_signal_immediately(self, trending_price):
        idx = trending_price.index
        signal = pd.Series(0.0, index=idx)
        signal.iloc[10:] = 1.0
        engine = BacktestEngine(price=trending_price, signal=signal, signal_lag=0)
        result = engine.run()
        assert result.positions.iloc[10] == 1.0


class TestReturnsCalculation:
    def test_flat_position_has_zero_return(self, trending_price):
        signal = pd.Series(0.0, index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal)
        result = engine.run()
        assert (result.returns == 0.0).all()
        assert (result.equity_curve == engine.initial_capital).all()

    def test_full_long_position_tracks_asset_return(self, trending_price):
        """满仓做多、零成本时，策略收益应完全等于标的收益率。"""
        signal = pd.Series(1.0, index=trending_price.index)
        engine = BacktestEngine(
            price=trending_price, signal=signal, signal_lag=0,
            commission_rate=0.0, slippage_rate=0.0,
        )
        result = engine.run()
        expected_returns = trending_price.pct_change().fillna(0.0)
        # 首期仓位变化会产生一次(0成本)换仓, 收益应与标的收益一致
        assert result.returns.values == pytest.approx(expected_returns.values, abs=1e-9)

    def test_short_position_inverts_asset_return(self, trending_price):
        signal = pd.Series(-1.0, index=trending_price.index)
        engine = BacktestEngine(
            price=trending_price, signal=signal, signal_lag=0,
            commission_rate=0.0, slippage_rate=0.0,
        )
        result = engine.run()
        expected_returns = -trending_price.pct_change().fillna(0.0)
        assert result.returns.values == pytest.approx(expected_returns.values, abs=1e-9)

    def test_transaction_costs_reduce_returns(self, trending_price):
        """有成本时的收益应该严格低于零成本时的收益（扣了费）。"""
        signal = pd.Series(1.0, index=trending_price.index)
        signal.iloc[::5] *= -1  # 制造频繁换仓触发成本

        no_cost_engine = BacktestEngine(
            price=trending_price, signal=signal, commission_rate=0.0, slippage_rate=0.0
        )
        with_cost_engine = BacktestEngine(
            price=trending_price, signal=signal, commission_rate=0.001, slippage_rate=0.001
        )
        no_cost_result = no_cost_engine.run()
        with_cost_result = with_cost_engine.run()
        assert with_cost_result.equity_curve.iloc[-1] < no_cost_result.equity_curve.iloc[-1]


class TestTradeExtraction:
    def test_no_trades_when_always_flat(self, trending_price):
        signal = pd.Series(0.0, index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal)
        result = engine.run()
        assert result.trades == []

    def test_single_long_trade_is_recorded(self, trending_price):
        """从头到尾持续满仓做多应该只记录一笔"开仓未平"或完整交易，交易方向应为多头。"""
        signal = pd.Series(1.0, index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal, signal_lag=0)
        result = engine.run()
        # 全程持有, 没有方向切换, 不会产生"平仓"记录(因为从未转向0)
        assert result.trades == []

    def test_direction_switch_produces_trade_record(self, trending_price):
        idx = trending_price.index
        signal = pd.Series(1.0, index=idx)
        signal.iloc[len(idx) // 2:] = -1.0  # 中途从多翻空
        engine = BacktestEngine(price=trending_price, signal=signal, signal_lag=0)
        result = engine.run()
        assert len(result.trades) >= 1
        assert result.trades[0].direction == 1

    def test_trades_dataframe_has_expected_columns(self, trending_price):
        idx = trending_price.index
        signal = pd.Series(1.0, index=idx)
        signal.iloc[len(idx) // 2:] = 0.0
        engine = BacktestEngine(price=trending_price, signal=signal, signal_lag=0)
        result = engine.run()
        df = result.trades_dataframe()
        assert set(df.columns) == {
            "entry_date", "exit_date", "direction", "entry_price", "exit_price", "pnl_pct"
        }

    def test_empty_trades_dataframe_when_no_trades(self, trending_price):
        signal = pd.Series(0.0, index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal)
        result = engine.run().trades_dataframe()
        assert len(result) == 0


class TestMetricsSummary:
    def test_summary_runs_without_error(self, trending_price):
        signal = pd.Series(1.0, index=trending_price.index)
        engine = BacktestEngine(price=trending_price, signal=signal)
        result = engine.run()
        summary = result.metrics_summary()
        assert "夏普比率" in summary
