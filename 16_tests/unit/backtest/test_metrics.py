# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pytest

from quant_system.backtest import metrics as M


class TestEquityReturnsConversion:
    def test_roundtrip(self, dates):
        returns = pd.Series([0.0, 0.01, -0.02, 0.03], index=dates[:4])
        equity = M.equity_from_returns(returns, initial_capital=100)
        back = M.returns_from_equity(equity)
        # 首项因为是pct_change的第一个差分点, fillna(0)后应与原始returns近似(除首项)
        assert back.iloc[1:].values == pytest.approx(returns.iloc[1:].values, abs=1e-9)


class TestTotalAndAnnualizedReturn:
    def test_total_return_known_value(self, dates):
        equity = pd.Series([100, 110, 121], index=dates[:3])
        assert M.total_return(equity) == pytest.approx(0.21)

    def test_total_return_too_short(self, dates):
        assert M.total_return(pd.Series([100], index=dates[:1])) == 0.0

    def test_annualized_return_known_value(self):
        """
        253个数据点 = 252期(n_periods=len-1)，刚好对应1年(252个交易日)，
        净值从100翻倍到200 -> 年化收益应精确等于100%。
        """
        equity = pd.Series(np.linspace(100, 200, 253))
        result = M.annualized_return(equity, periods_per_year=252)
        assert result == pytest.approx(1.0, abs=1e-6)

    def test_annualized_return_handles_total_loss(self):
        equity = pd.Series([100, 50, 0])
        result = M.annualized_return(equity, periods_per_year=252)
        assert result == -1.0


class TestVolatilityAndSharpe:
    def test_sharpe_positive_for_consistent_gains(self):
        returns = pd.Series([0.01] * 50)
        # 恒定收益率, std=0 -> sharpe按定义返回0(避免除零)
        assert M.sharpe_ratio(returns) == 0.0

    def test_sharpe_with_known_values(self):
        """
        人工构造均值为正、有波动的收益率序列, 验证夏普比率公式。
        """
        returns = pd.Series([0.02, -0.01, 0.015, -0.005, 0.01])
        rf = 0.0
        expected = (returns.mean() / returns.std(ddof=1)) * np.sqrt(252)
        assert M.sharpe_ratio(returns, risk_free_rate=rf) == pytest.approx(expected)

    def test_sortino_only_penalizes_downside(self):
        """
        两组收益率总体标准差相同，但一组上行波动大、一组下行波动大，
        索提诺比率应该不同（sortino只用下行标准差）。
        """
        upside_vol = pd.Series([0.05, 0.05, -0.01, -0.01, -0.01])
        downside_vol = pd.Series([0.01, 0.01, -0.05, -0.05, -0.01])
        sortino_up = M.sortino_ratio(upside_vol)
        sortino_down = M.sortino_ratio(downside_vol)
        assert sortino_up != sortino_down

    def test_sortino_no_downside_returns_zero(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        assert M.sortino_ratio(returns) == 0.0


class TestMaxDrawdown:
    def test_known_drawdown(self):
        equity = pd.Series([100, 120, 90, 110])
        # peak=120, trough=90 -> dd = 90/120-1 = -0.25
        assert M.max_drawdown(equity) == pytest.approx(-0.25)

    def test_monotonic_rise_has_zero_drawdown(self):
        equity = pd.Series([100, 110, 120])
        assert M.max_drawdown(equity) == pytest.approx(0.0)

    def test_max_drawdown_duration(self):
        equity = pd.Series([100, 90, 95, 85, 105, 100])
        # 回撤状态: idx1(90<100)=T,idx2(95<100)=T,idx3(85<100)=T,idx4(105>=100,新高)=F,idx5(100<105)=T
        # 最长连续回撤段: idx1-3连续3期
        assert M.max_drawdown_duration(equity) == 3


class TestCalmarRatio:
    def test_zero_drawdown_returns_zero(self):
        equity = pd.Series(np.linspace(100, 200, 50))
        assert M.calmar_ratio(equity) == 0.0


class TestWinRateAndProfitLoss:
    def test_win_rate_known_value(self):
        trade_returns = pd.Series([0.05, -0.02, 0.03, -0.01])
        assert M.win_rate(trade_returns) == pytest.approx(0.5)

    def test_win_rate_empty(self):
        assert M.win_rate(pd.Series(dtype=float)) == 0.0

    def test_profit_loss_ratio_known_value(self):
        trade_returns = pd.Series([0.10, 0.20, -0.05, -0.15])
        # avg_win=0.15, avg_loss=0.10 -> ratio=1.5
        assert M.profit_loss_ratio(trade_returns) == pytest.approx(1.5)

    def test_profit_loss_ratio_no_losses_returns_zero(self):
        trade_returns = pd.Series([0.1, 0.2])
        assert M.profit_loss_ratio(trade_returns) == 0.0


class TestSummary:
    def test_summary_contains_expected_keys(self, rising_equity):
        result = M.summary(rising_equity)
        expected_keys = {
            "总收益率", "年化收益率", "年化波动率", "夏普比率",
            "索提诺比率", "最大回撤", "最大回撤持续期", "卡玛比率",
        }
        assert expected_keys.issubset(result.keys())

    def test_summary_includes_trade_stats_when_provided(self, rising_equity):
        trade_returns = pd.Series([0.05, -0.02])
        result = M.summary(rising_equity, trade_returns=trade_returns)
        assert "交易次数" in result
        assert result["交易次数"] == 2
