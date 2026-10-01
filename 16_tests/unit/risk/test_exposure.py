# -*- coding: utf-8 -*-
import pytest

from quant_system.risk.exposure import (
    calculate_exposure,
    calculate_sector_exposure,
    Exposure,
    PositionLimiter,
    ConcentrationLimiter,
    GrossNetExposureLimiter,
    SectorExposureLimiter,
)


class TestCalculateExposure:
    def test_long_and_short_split_correctly(self):
        positions = {"AAPL": 100, "TSLA": -50}
        prices = {"AAPL": 150, "TSLA": 200}
        result = calculate_exposure(positions, prices)
        assert result.long_value == pytest.approx(15000)
        assert result.short_value == pytest.approx(10000)
        assert result.gross_value == pytest.approx(25000)
        assert result.net_value == pytest.approx(5000)

    def test_missing_price_raises(self):
        with pytest.raises(ValueError):
            calculate_exposure({"AAPL": 100}, prices={})

    def test_invalid_positions_type_raises(self):
        with pytest.raises(TypeError):
            calculate_exposure([1, 2, 3])

    def test_dict_with_embedded_price(self):
        positions = {"AAPL": {"quantity": 100, "price": 150}}
        result = calculate_exposure(positions)
        assert result.long_value == pytest.approx(15000)


class TestCalculateSectorExposure:
    def test_groups_by_sector(self):
        positions = {"AAPL": 100, "MSFT": 50, "XOM": -30}
        prices = {"AAPL": 150, "MSFT": 300, "XOM": 100}
        sectors = {"AAPL": "Tech", "MSFT": "Tech", "XOM": "Energy"}
        result = calculate_sector_exposure(positions, prices, sectors)
        assert result["Tech"].long_value == pytest.approx(100 * 150 + 50 * 300)
        assert result["Energy"].short_value == pytest.approx(3000)

    def test_unknown_sector_bucket(self):
        positions = {"AAPL": 100}
        prices = {"AAPL": 150}
        result = calculate_sector_exposure(positions, prices)
        assert "UNKNOWN" in result


class TestPositionLimiter:
    def test_no_limit_passes_through(self):
        limiter = PositionLimiter(None)
        assert limiter.limit(12345) == 12345

    def test_clips_to_max_preserving_sign(self):
        limiter = PositionLimiter(100)
        assert limiter.limit(150) == 100
        assert limiter.limit(-150) == -100
        assert limiter.limit(50) == 50

    def test_negative_max_position_raises(self):
        with pytest.raises(ValueError):
            PositionLimiter(-1)

    def test_check(self):
        limiter = PositionLimiter(100)
        assert limiter.check(50) is True
        assert limiter.check(150) is False


class TestConcentrationLimiter:
    def test_requires_at_least_one_limit(self):
        with pytest.raises(ValueError):
            ConcentrationLimiter()

    def test_invalid_max_weight_range_raises(self):
        with pytest.raises(ValueError):
            ConcentrationLimiter(max_weight=1.5)

    def test_limit_quantity_respects_weight_cap(self):
        limiter = ConcentrationLimiter(max_weight=0.1)
        # portfolio_gross_value=100万, cap=10万; price=50 -> 最多2000股
        qty = limiter.limit_quantity("AAPL", quantity=5000, price=50, portfolio_gross_value=1_000_000)
        assert qty == pytest.approx(2000)

    def test_limit_quantity_preserves_sign_for_short(self):
        limiter = ConcentrationLimiter(max_weight=0.1)
        qty = limiter.limit_quantity("AAPL", quantity=-5000, price=50, portfolio_gross_value=1_000_000)
        assert qty == pytest.approx(-2000)

    def test_check_within_limit(self):
        limiter = ConcentrationLimiter(max_weight=0.2)
        assert limiter.check(position_value=150_000, portfolio_gross_value=1_000_000) is True
        assert limiter.check(position_value=250_000, portfolio_gross_value=1_000_000) is False

    def test_check_zero_total_with_zero_position(self):
        """total=0 且 v=0 时不应除零，应判定为通过。"""
        limiter = ConcentrationLimiter(max_weight=0.2)
        assert limiter.check(position_value=0, portfolio_gross_value=0) is True


class TestGrossNetExposureLimiter:
    def test_passes_within_limits(self):
        limiter = GrossNetExposureLimiter(max_gross=50000, max_net=20000)
        positions = {"AAPL": 100, "TSLA": -50}
        prices = {"AAPL": 150, "TSLA": 200}
        assert limiter.check(positions, prices) is True

    def test_fails_when_gross_exceeds(self):
        limiter = GrossNetExposureLimiter(max_gross=10000)
        positions = {"AAPL": 100}
        prices = {"AAPL": 150}
        assert limiter.check(positions, prices) is False

    def test_negative_limits_raise(self):
        with pytest.raises(ValueError):
            GrossNetExposureLimiter(max_gross=-1)


class TestSectorExposureLimiter:
    def test_check_flags_sector_over_limit(self):
        limiter = SectorExposureLimiter(sector_limits={"Tech": 10000})
        positions = {"AAPL": 100}
        prices = {"AAPL": 150}
        sectors = {"AAPL": "Tech"}
        result = limiter.check(positions, prices, sectors)
        assert result["Tech"].allowed is False

    def test_apply_scales_down_overlimit_sector(self):
        limiter = SectorExposureLimiter(sector_limits={"Tech": 5000})
        positions = {"AAPL": {"quantity": 100, "price": 150, "sector": "Tech"}}
        result = limiter.apply(positions)
        # 5000/150 = 33.33 应该被裁剪到这个范围内
        assert abs(result["AAPL"]) <= 5000 / 150 + 1e-6

    def test_negative_sector_limit_raises(self):
        with pytest.raises(ValueError):
            SectorExposureLimiter(sector_limits={"Tech": -1})

    def test_apply_requires_mapping(self):
        limiter = SectorExposureLimiter()
        with pytest.raises(TypeError):
            limiter.apply([1, 2, 3])
