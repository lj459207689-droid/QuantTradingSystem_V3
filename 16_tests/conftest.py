# -*- coding: utf-8 -*-
"""
共享 fixture。放在 16_tests/ 根目录下，pytest 会自动发现。
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def dates():
    """100 个交易日的日期索引。"""
    return pd.date_range("2024-01-01", periods=100, freq="B")


@pytest.fixture
def flat_returns(dates):
    """全部为 0 的收益率序列，用于验证边界情况。"""
    return pd.Series(0.0, index=dates)


@pytest.fixture
def known_returns(dates):
    """
    固定的收益率序列（不是随机数），这样测试结果可预测、可重复。
    手工构造：100 期里有 95 期是 +0.01，5 期是 -0.05（模拟肥尾分布），
    用来验证历史模拟法 VaR/CVaR 的分位数计算是否正确。
    """
    values = [0.01] * 95 + [-0.05] * 5
    return pd.Series(values, index=dates)


@pytest.fixture
def rising_equity(dates):
    """单调上涨的净值曲线，无回撤。"""
    values = np.linspace(1_000_000, 1_500_000, len(dates))
    return pd.Series(values, index=dates)


@pytest.fixture
def equity_with_drawdown(dates):
    """
    手工构造一条先涨后跌再涨的净值曲线，最大回撤精确可算：
    从 peak=1,200,000 跌到 trough=960,000，回撤 = (1,200,000-960,000)/1,200,000 = 0.20
    """
    n = len(dates)
    values = np.ones(n) * 1_000_000.0
    values[:20] = np.linspace(1_000_000, 1_200_000, 20)   # 上涨到峰值
    values[20:40] = np.linspace(1_200_000, 960_000, 20)   # 下跌到谷底(回撤20%)
    values[40:] = np.linspace(960_000, 1_100_000, n - 40)  # 部分修复
    return pd.Series(values, index=dates)


@pytest.fixture
def trending_price(dates):
    """单调上涨的价格序列，涨幅 20%。"""
    values = np.linspace(100.0, 120.0, len(dates))
    return pd.Series(values, index=dates)
