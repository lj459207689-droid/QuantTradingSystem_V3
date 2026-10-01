# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pytest

from quant_system.risk.cvar import (
    historical_cvar,
    parametric_cvar,
    rolling_cvar,
    cvar_to_var_ratio,
)
from quant_system.risk.var import historical_var


class TestHistoricalCvar:
    def test_known_tail_average(self, known_returns):
        """
        95期+0.01、5期-0.05。95%置信度下 VaR 对应第5百分位，
        尾部(比VaR更差的样本)应恰好是那5期 -0.05，CVaR = 0.05。
        """
        result = historical_cvar(known_returns, confidence=0.95)
        assert result == pytest.approx(0.05, abs=1e-6)

    def test_cvar_is_never_smaller_than_var(self, known_returns):
        """定义上 CVaR(平均尾部损失) 应该 >= VaR(分位点损失)。"""
        var = historical_var(known_returns, confidence=0.95)
        cvar = historical_cvar(known_returns, confidence=0.95)
        assert cvar >= var - 1e-9

    def test_empty_series_returns_zero(self):
        assert historical_cvar(pd.Series(dtype=float)) == 0.0

    def test_degenerates_to_var_when_no_tail_samples(self, dates):
        """
        数据量太少、没有比 VaR 更差的样本时，应退化为用 VaR 本身近似，
        而不是报错或返回 NaN。
        """
        s = pd.Series([0.01, 0.02, 0.015], index=dates[:3])
        var = historical_var(s, confidence=0.95)
        cvar = historical_cvar(s, confidence=0.95)
        assert cvar == pytest.approx(var)


class TestParametricCvar:
    def test_matches_analytical_formula(self, known_returns):
        from scipy import stats
        mu = known_returns.mean()
        sigma = known_returns.std(ddof=1)
        alpha = 0.05
        z = stats.norm.ppf(alpha)
        expected = max(-(mu - sigma * stats.norm.pdf(z) / alpha), 0.0)
        result = parametric_cvar(known_returns, confidence=0.95)
        assert result == pytest.approx(expected)

    def test_insufficient_data_returns_zero(self):
        assert parametric_cvar(pd.Series([0.01])) == 0.0


class TestRollingCvar:
    def test_invalid_method_raises(self, known_returns):
        with pytest.raises(ValueError):
            rolling_cvar(known_returns, method="bad")

    def test_output_length(self, known_returns):
        result = rolling_cvar(known_returns, window=20)
        assert len(result) == len(known_returns)


class TestCvarToVarRatio:
    def test_ratio_at_least_one(self, dates):
        """
        用尾部更厚的分布（20%极端亏损样本），确保VaR本身不是0，
        这样才能有意义地验证 CVaR/VaR >= 1。
        """
        values = [0.01] * 80 + [-0.10] * 20
        s = pd.Series(values, index=dates)
        ratio = cvar_to_var_ratio(s, confidence=0.95)
        assert ratio >= 1.0 - 1e-9

    def test_zero_var_returns_zero(self, dates):
        """VaR为0时不应抛出除零异常，而是返回0。"""
        s = pd.Series([0.05] * len(dates), index=dates)  # 全正收益, VaR=0
        assert cvar_to_var_ratio(s, confidence=0.5) == 0.0
