# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pytest

from quant_system.risk.var import (
    historical_var,
    parametric_var,
    monte_carlo_var,
    rolling_var,
    var_to_dollar,
)


class TestHistoricalVar:
    def test_known_quantile(self, known_returns):
        """
        95期+0.01、5期-0.05，95%置信度对应的是第5百分位数。
        5个-0.05排在最前面，第5百分位数的插值点刚好落在"由负转正"的
        边界附近、略偏正值一侧，所以 -percentile 是负数，会被 max(.,0) clip为0。
        用 numpy 独立算一遍分位数做交叉验证，而不是重复实现的逻辑。
        """
        expected = max(-np.percentile(known_returns.values, 5), 0.0)
        result = historical_var(known_returns, confidence=0.95)
        assert result == pytest.approx(expected)

    def test_known_quantile_with_heavier_tail(self, dates):
        """
        构造尾部更极端的分布(左尾更厚)，确保5百分位数本身就是负收益，
        这样 VaR 不会被 clip 到 0，可以验证一个"正常不触发clip"的场景。
        """
        values = [0.01] * 80 + [-0.10] * 20  # 20%的极端亏损样本
        s = pd.Series(values, index=dates)
        expected = max(-np.percentile(s.values, 5), 0.0)
        result = historical_var(s, confidence=0.95)
        assert result == pytest.approx(expected)
        assert result > 0

    def test_empty_series_returns_zero(self):
        assert historical_var(pd.Series(dtype=float)) == 0.0

    def test_all_nan_returns_zero(self):
        s = pd.Series([np.nan, np.nan])
        assert historical_var(s) == 0.0

    def test_window_restricts_to_recent_data(self, dates):
        """
        前50期全是极端亏损，后10期全是温和盈利；window=10 应只看后10期，
        忽略前面的极端亏损数据。全正收益区间算出的 VaR 会被 clip 到 0，
        这里重点验证的是"确实只用了最近10期"而不是把前面的-0.5也算进去
        （如果错误地用了全部60期，5百分位数会是很大的负收益，VaR会远大于0）。
        """
        values = [-0.5] * 50 + [0.01] * 50
        s = pd.Series(values, index=dates)
        result = historical_var(s, confidence=0.95, window=10)
        assert result == pytest.approx(0.0)

    def test_never_negative(self, dates):
        """VaR 定义上不应为负（max(var, 0.0) 保护）。"""
        s = pd.Series([0.05] * len(dates), index=dates)  # 全部是正收益
        assert historical_var(s, confidence=0.5) >= 0


class TestParametricVar:
    def test_matches_normal_formula(self, known_returns):
        from scipy import stats
        mu = known_returns.mean()
        sigma = known_returns.std(ddof=1)
        z = stats.norm.ppf(0.05)
        expected = max(-(mu + z * sigma), 0.0)
        result = parametric_var(known_returns, confidence=0.95)
        assert result == pytest.approx(expected)

    def test_insufficient_data_returns_zero(self):
        assert parametric_var(pd.Series([0.01])) == 0.0
        assert parametric_var(pd.Series(dtype=float)) == 0.0

    def test_zero_volatility_is_non_negative(self, dates):
        """标准差为0时(所有收益率相同)，结果不应是负数或报错。"""
        s = pd.Series([0.02] * len(dates), index=dates)
        result = parametric_var(s, confidence=0.95)
        assert result >= 0


class TestMonteCarloVar:
    def test_seed_makes_result_reproducible(self, known_returns):
        r1 = monte_carlo_var(known_returns, confidence=0.95, n_simulations=5000, seed=42)
        r2 = monte_carlo_var(known_returns, confidence=0.95, n_simulations=5000, seed=42)
        assert r1 == r2

    def test_converges_near_parametric_var(self, known_returns):
        """
        蒙特卡洛法基于同样的正态假设(mu/sigma)抽样，大样本量下应收敛到
        接近 parametric_var 的结果(允许一定抽样误差)。
        """
        mc = monte_carlo_var(known_returns, confidence=0.95, n_simulations=200_000, seed=1)
        param = parametric_var(known_returns, confidence=0.95)
        assert mc == pytest.approx(param, abs=0.01)

    def test_insufficient_data_returns_zero(self):
        assert monte_carlo_var(pd.Series([0.01])) == 0.0


class TestRollingVar:
    def test_invalid_method_raises(self, known_returns):
        with pytest.raises(ValueError):
            rolling_var(known_returns, method="not_a_method")

    def test_output_length_matches_input(self, known_returns):
        result = rolling_var(known_returns, window=20, method="historical")
        assert len(result) == len(known_returns)
        # 前 window-1 期应为 NaN(数据不足)
        assert result.iloc[:19].isna().all()
        assert result.iloc[19:].notna().all()

    def test_naming(self, known_returns):
        result = rolling_var(known_returns, confidence=0.95, window=20, method="parametric")
        assert result.name == "var_95_parametric"


class TestVarToDollar:
    def test_simple_conversion(self):
        assert var_to_dollar(0.025, 1_000_000) == pytest.approx(25_000)

    def test_zero_portfolio_value(self):
        assert var_to_dollar(0.05, 0) == 0.0
