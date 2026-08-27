"""
Unit tests for SMA and EMA.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_system.factors import EMA, SMA

# ======================================================================
# SMA Tests
# ======================================================================


def test_sma_initial_state() -> None:
    """SMA 初始状态应该为空。"""

    factor = SMA(period=3)

    assert factor.name == "sma_3"
    assert factor.category == "trend"
    assert factor.value is None
    assert factor.is_ready is False


def test_sma_update() -> None:
    """测试 SMA 流式更新。"""

    factor = SMA(period=3)

    assert factor.update(10) is None
    assert factor.value is None

    assert factor.update(20) is None
    assert factor.value is None

    assert factor.update(30) == pytest.approx(20.0)
    assert factor.value == pytest.approx(20.0)

    assert factor.update(40) == pytest.approx(30.0)
    assert factor.value == pytest.approx(30.0)


def test_sma_sliding_window() -> None:
    """测试 SMA 滑动窗口。"""

    factor = SMA(period=3)

    values = [10, 20, 30, 40, 50]

    results = [
        factor.update(value)
        for value in values
    ]

    assert results[0] is None
    assert results[1] is None
    assert results[2] == pytest.approx(20.0)
    assert results[3] == pytest.approx(30.0)
    assert results[4] == pytest.approx(40.0)


def test_sma_dataframe_calculate() -> None:
    """测试 SMA 历史 DataFrame 批量计算。"""

    factor = SMA(period=3)

    data = pd.DataFrame(
        {
            "close": [
                10,
                20,
                30,
                40,
                50,
            ]
        }
    )

    result = factor.calculate(data)

    assert len(result) == 5

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])

    assert result.iloc[2] == pytest.approx(20.0)
    assert result.iloc[3] == pytest.approx(30.0)
    assert result.iloc[4] == pytest.approx(40.0)


def test_sma_reset() -> None:
    """测试 SMA reset。"""

    factor = SMA(period=3)

    factor.update(10)
    factor.update(20)
    factor.update(30)

    assert factor.value == pytest.approx(20.0)

    factor.reset()

    assert factor.value is None
    assert factor.is_ready is False

    assert factor.update(10) is None


# ======================================================================
# EMA Tests
# ======================================================================


def test_ema_initial_state() -> None:
    """EMA 初始状态应该为空。"""

    factor = EMA(period=3)

    assert factor.name == "ema_3"
    assert factor.category == "trend"
    assert factor.value is None
    assert factor.is_ready is False


def test_ema_update() -> None:
    """测试 EMA 流式更新。"""

    factor = EMA(period=3)

    assert factor.update(10) is None
    assert factor.update(20) is None

    # 第三个数据：
    # SMA = (10 + 20 + 30) / 3 = 20
    assert factor.update(30) == pytest.approx(20.0)

    # alpha = 2 / (3 + 1) = 0.5
    #
    # EMA = 0.5 * 40 + 0.5 * 20
    #     = 30
    assert factor.update(40) == pytest.approx(30.0)

    assert factor.value == pytest.approx(30.0)


def test_ema_calculation() -> None:
    """测试 EMA 批量计算。"""

    factor = EMA(period=3)

    data = pd.DataFrame(
        {
            "close": [
                10,
                20,
                30,
                40,
                50,
            ]
        }
    )

    result = factor.calculate(data)

    assert len(result) == 5

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])

    assert result.iloc[2] == pytest.approx(20.0)
    assert result.iloc[3] == pytest.approx(30.0)
    assert result.iloc[4] == pytest.approx(40.0)


def test_ema_reset() -> None:
    """测试 EMA reset。"""

    factor = EMA(period=3)

    factor.update(10)
    factor.update(20)
    factor.update(30)

    assert factor.value == pytest.approx(20.0)

    factor.reset()

    assert factor.value is None
    assert factor.is_ready is False

    assert factor.update(10) is None


# ======================================================================
# Interface Tests
# ======================================================================


def test_sma_and_ema_are_factor_instances() -> None:
    """确保 SMA / EMA 都遵循 Factor 接口。"""

    from quant_system.core.interfaces.factor import Factor

    sma = SMA(period=5)
    ema = EMA(period=5)

    assert isinstance(sma, Factor)
    assert isinstance(ema, Factor)


def test_sma_ema_metadata() -> None:
    """测试 Factor metadata。"""

    sma = SMA(period=20)
    ema = EMA(period=20)

    assert sma.metadata["name"] == "sma_20"
    assert sma.metadata["category"] == "trend"

    assert ema.metadata["name"] == "ema_20"
    assert ema.metadata["category"] == "trend"


def test_invalid_period() -> None:
    """周期必须大于 0。"""

    with pytest.raises(ValueError):
        SMA(period=0)

    with pytest.raises(ValueError):
        EMA(period=0)

    with pytest.raises(ValueError):
        SMA(period=-1)

    with pytest.raises(ValueError):
        EMA(period=-1)


def test_invalid_dataframe_field() -> None:
    """DataFrame 缺少 close 字段时应该报错。"""

    factor = SMA(period=3)

    data = pd.DataFrame(
        {
            "open": [10, 20, 30],
        }
    )

    with pytest.raises(ValueError):
        factor.calculate(data)


def test_sma_numeric_stream() -> None:
    """SMA 应该支持直接输入数字。"""

    factor = SMA(period=3)

    assert factor.update(10) is None
    assert factor.update(20) is None
    assert factor.update(30) == pytest.approx(20.0)


def test_ema_numeric_stream() -> None:
    """EMA 应该支持直接输入数字。"""

    factor = EMA(period=3)

    assert factor.update(10) is None
    assert factor.update(20) is None
    assert factor.update(30) == pytest.approx(20.0)
