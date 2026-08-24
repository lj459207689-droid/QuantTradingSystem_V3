"""
Preprocessing pipeline: chains cleaner -> missing -> outlier -> adjust
into one configurable call, so 05_factors has a single entry point
instead of wiring five modules together by hand every time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import pandas as pd

from .adjust import AdjustmentMethod, PriceAdjuster
from .cleaner import DataCleaner
from .missing import MissingValueHandler
from .outlier import OutlierDetector

if TYPE_CHECKING:
    from quant_system.common.calendar import TradingCalendar


@dataclass
class PreprocessConfig:
    """Toggle/tune each stage of the pipeline."""

    # cleaner
    dedup: bool = True
    drop_invalid_ohlc: bool = True

    # missing
    handle_missing: bool = False
    # Preferred for daily bars: pass a real TradingCalendar so
    # weekends/holidays are correctly excluded from "expected" days.
    calendar: Optional["TradingCalendar"] = field(default=None, repr=False)
    # Fallback when no calendar is available (or for intraday bars):
    # a naive pandas freq string, e.g. '1D', '5min'. Ignored if
    # `calendar` is set.
    missing_freq: Optional[str] = None
    max_missing_ratio: Optional[float] = None  # drop the whole series if exceeded

    # outlier
    detect_outliers: bool = True
    outlier_method: str = "zscore"           # "zscore" | "iqr"
    outlier_window: int = 20
    outlier_threshold: float = 4.0
    outlier_action: str = "interpolate"      # "interpolate" | "remove"

    # adjust
    adjust_method: AdjustmentMethod = AdjustmentMethod.NONE
    corporate_actions: Optional[pd.DataFrame] = field(default=None, repr=False)


class PreprocessPipeline:
    """
    Runs the configured stages, in a fixed, deliberate order:

    1. clean       (structural validity, dedup)
    2. missing     (gap filling, optional)
    3. outlier     (statistical bad-tick detection, optional)
    4. adjust      (splits/dividends, optional)

    Order matters: outlier detection runs on return series, so it
    should happen before adjustment distorts historical price levels
    with cumulative split/dividend factors; missing-value filling
    happens before outlier detection so filled bars don't get
    flagged as outliers just for being flat/no-trade bars.
    """

    def __init__(self, config: Optional[PreprocessConfig] = None) -> None:
        self.config = config or PreprocessConfig()

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        config = self.config

        # 1. Clean
        result = DataCleaner.clean(
            result,
            drop_invalid=config.drop_invalid_ohlc,
            dedup=config.dedup,
        )

        if result.empty:
            return result

        # 2. Missing values
        if config.handle_missing:
            if config.calendar is not None:
                if config.max_missing_ratio is not None:
                    ratio = MissingValueHandler.missing_ratio_calendar(
                        result, config.calendar
                    )
                    if ratio > config.max_missing_ratio:
                        return result.iloc[0:0]  # too sparse - return empty

                result = MissingValueHandler.reindex_to_calendar(
                    result, config.calendar
                )
                result = MissingValueHandler.forward_fill_prices(result)

            elif config.missing_freq:
                if config.max_missing_ratio is not None:
                    checked = MissingValueHandler.drop_if_missing_ratio_exceeds(
                        result, config.missing_freq, config.max_missing_ratio
                    )
                    if checked is None:
                        return result.iloc[0:0]  # too sparse - return empty

                result = MissingValueHandler.reindex_to_frequency(
                    result, config.missing_freq
                )
                result = MissingValueHandler.forward_fill_prices(result)

            else:
                raise ValueError(
                    "PreprocessConfig.handle_missing=True requires "
                    "either `calendar` or `missing_freq` to be set"
                )

        # 3. Outliers
        if config.detect_outliers and len(result) > 1:
            if config.outlier_method == "zscore":
                mask = OutlierDetector.detect_by_return_zscore(
                    result,
                    window=config.outlier_window,
                    threshold=config.outlier_threshold,
                )
            elif config.outlier_method == "iqr":
                mask = OutlierDetector.detect_by_iqr(result)
            else:
                raise ValueError(
                    f"Unsupported outlier_method: {config.outlier_method}"
                )

            if mask.any():
                if config.outlier_action == "remove":
                    result = OutlierDetector.remove_outliers(result, mask)
                elif config.outlier_action == "interpolate":
                    result = OutlierDetector.interpolate_outliers(result, mask)
                else:
                    raise ValueError(
                        f"Unsupported outlier_action: {config.outlier_action}"
                    )

        # 4. Adjustment
        if config.adjust_method != AdjustmentMethod.NONE:
            result = PriceAdjuster.apply(
                result,
                corporate_actions=config.corporate_actions,
                method=config.adjust_method,
            )

        return result.reset_index(drop=True)
