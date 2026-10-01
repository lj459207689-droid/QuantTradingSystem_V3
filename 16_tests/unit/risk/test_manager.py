# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from quant_system.risk.manager import RiskManager, RiskDecision


def make_order(**overrides):
    base = dict(symbol="AAPL", side="BUY", quantity=100, price=150.0)
    base.update(overrides)
    return base


def make_portfolio(**overrides):
    base = dict(cash=100_000.0, equity=1_000_000.0, positions={})
    base.update(overrides)
    return base


class TestCheckOrderBasicValidation:
    def test_valid_order_is_allowed(self):
        rm = RiskManager(max_position=0.5, max_order_value=None)
        decision = rm.check_order(
            make_order(), make_portfolio(), current_drawdown=0.0
        )
        assert decision.allowed is True
        assert decision.approved_quantity == 100

    def test_trading_not_allowed_rejects(self):
        rm = RiskManager()
        decision = rm.check_order(
            make_order(), make_portfolio(), trading_allowed=False, current_drawdown=0.0
        )
        assert decision.allowed is False
        assert "禁止下单" in decision.reason

    def test_missing_symbol_rejects(self):
        rm = RiskManager()
        decision = rm.check_order(
            make_order(symbol=""), make_portfolio(), current_drawdown=0.0
        )
        assert decision.allowed is False
        assert "symbol" in decision.reason

    def test_nonpositive_quantity_rejects(self):
        rm = RiskManager()
        decision = rm.check_order(
            make_order(quantity=0), make_portfolio(), current_drawdown=0.0
        )
        assert decision.allowed is False

    def test_nonpositive_price_rejects(self):
        rm = RiskManager()
        decision = rm.check_order(
            make_order(price=0), make_portfolio(), current_drawdown=0.0
        )
        assert decision.allowed is False


class TestCheckOrderValueLimit:
    def test_exceeding_max_order_value_rejects(self):
        rm = RiskManager(max_order_value=5000)
        decision = rm.check_order(
            make_order(quantity=100, price=150),  # order_value = 15000
            make_portfolio(),
            current_drawdown=0.0,
        )
        assert decision.allowed is False
        assert "max_order_value" in decision.reason

    def test_construction_rejects_nonpositive_max_order_value(self):
        with pytest.raises(ValueError):
            RiskManager(max_order_value=0)


class TestCheckOrderCashBuffer:
    def test_insufficient_cash_rejects_buy(self):
        rm = RiskManager(min_cash_buffer=0.0)
        decision = rm.check_order(
            make_order(quantity=1000, price=150),  # order_value=150000 > cash
            make_portfolio(cash=100_000),
            current_drawdown=0.0,
        )
        assert decision.allowed is False
        assert "现金" in decision.reason

    def test_missing_cash_with_fail_closed_rejects_buy(self):
        """fail_closed=True 时，缺少 cash 字段应该拒单而不是放行（安全默认）。"""
        rm = RiskManager(fail_closed=True)
        portfolio = make_portfolio()
        del portfolio["cash"]
        decision = rm.check_order(make_order(), portfolio, current_drawdown=0.0)
        assert decision.allowed is False
        assert "cash" in decision.reason

    def test_missing_cash_with_fail_open_allows_buy(self):
        """fail_closed=False 时，缺少 cash 不应阻止下单（显式关闭保守模式）。"""
        rm = RiskManager(fail_closed=False, max_position=1.0)
        portfolio = make_portfolio()
        del portfolio["cash"]
        decision = rm.check_order(make_order(), portfolio, current_drawdown=0.0)
        assert decision.allowed is True

    def test_sell_side_does_not_require_cash_check(self):
        rm = RiskManager(fail_closed=True)
        portfolio = make_portfolio()
        del portfolio["cash"]
        decision = rm.check_order(
            make_order(side="SELL"), portfolio, current_drawdown=0.0
        )
        # SELL 不走 cash 分支，不应因缺 cash 被拒
        assert decision.checks.get("cash_limit") is True


class TestCheckOrderPositionLimit:
    def test_exceeding_max_position_weight_rejects(self):
        rm = RiskManager(max_position=0.1)
        decision = rm.check_order(
            make_order(quantity=1000, price=150),  # 150000/1000000=15% > 10%限制
            make_portfolio(equity=1_000_000, cash=1_000_000),
            current_drawdown=0.0,
        )
        assert decision.allowed is False
        assert "max_position" in decision.reason

    def test_missing_equity_with_fail_closed_rejects(self):
        rm = RiskManager(fail_closed=True)
        portfolio = make_portfolio()
        del portfolio["equity"]
        decision = rm.check_order(make_order(), portfolio, current_drawdown=0.0)
        assert decision.allowed is False
        assert "equity" in decision.reason

    def test_existing_position_is_included_in_projection(self):
        rm = RiskManager(max_position=0.2)
        portfolio = make_portfolio(
            equity=1_000_000, cash=1_000_000, positions={"AAPL": 1000}
        )
        # 已持1000股,再买100股,按150元计算 projected=1100*150/1000000=16.5% < 20%通过
        decision = rm.check_order(
            make_order(quantity=100, price=150), portfolio, current_drawdown=0.0
        )
        assert decision.metadata["current_position"] == 1000
        assert decision.metadata["projected_position"] == 1100


class TestCheckOrderDrawdownData:
    def test_negative_drawdown_rejects(self):
        rm = RiskManager()
        decision = rm.check_order(
            make_order(), make_portfolio(), current_drawdown=-0.01
        )
        assert decision.allowed is False

    def test_missing_drawdown_with_fail_closed_rejects(self):
        rm = RiskManager(fail_closed=True)
        decision = rm.check_order(make_order(), make_portfolio())  # current_drawdown=None
        assert decision.allowed is False
        assert "回撤" in decision.reason

    def test_missing_drawdown_with_fail_open_allows(self):
        rm = RiskManager(fail_closed=False)
        decision = rm.check_order(make_order(), make_portfolio())
        assert decision.allowed is True


class TestMonitor:
    def test_breach_detection(self, equity_with_drawdown):
        """
        monitor() 比较的是"当前(最后一期)回撤"而不是历史最大回撤；
        fixture 的净值曲线到最后已部分修复，当前回撤约为8.3%(历史最大回撤
        则是20%)，所以限额要设在当前回撤之下才会触发报警。
        """
        rm = RiskManager(
            var_limit=0.5, cvar_limit=0.5, max_drawdown_limit=0.05
        )  # var/cvar限额设宽松, 只测回撤
        report = rm.monitor(equity_with_drawdown)
        assert report.has_breach is True
        assert any("回撤" in alert for alert in report.alerts)
        # 报告里应同时能看到历史最大回撤(20%)这个独立指标
        assert report.metrics["历史最大回撤"] == pytest.approx(0.20, abs=1e-6)

    def test_no_breach_with_generous_limits(self, rising_equity):
        rm = RiskManager(var_limit=1.0, cvar_limit=1.0, max_drawdown_limit=1.0)
        report = rm.monitor(rising_equity)
        assert report.has_breach is False


class TestApplyPositionRisk:
    def test_combines_stoploss_and_position_limit(self, dates):
        rm = RiskManager(stop_loss_pct=0.08, max_position=50)
        position = pd.Series([100, 100], index=dates[:2])
        price = pd.Series([100, 100], index=dates[:2])
        result = rm.apply_position_risk(position, price)
        # 单标的仓位上限50生效
        assert (result.abs() <= 50).all()


class TestApplyDrawdownControl:
    def test_raises_without_configured_thresholds(self, dates):
        rm = RiskManager(drawdown_thresholds=None)
        position = pd.Series([1.0], index=dates[:1])
        equity = pd.Series([100.0], index=dates[:1])
        with pytest.raises(ValueError):
            rm.apply_drawdown_control(position, equity)
