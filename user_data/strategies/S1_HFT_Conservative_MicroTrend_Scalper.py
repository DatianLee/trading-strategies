from datetime import datetime
from typing import Any, Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import (
    IStrategy,
    DecimalParameter,
    IntParameter,
    merge_informative_pair,
)


class S1_HFT_Conservative_MicroTrend_Scalper(IStrategy):
    """
    S1: HFT Conservative Micro-Trend Scalper (1m base, 3m/5m context).

    Fee/slippage assumptions (used for risk calibration):
    - Taker fee: 0.04% per side (0.08% round trip).
    - Slippage: 0.03% per side during liquid sessions.
    - Combined friction budget ~= 0.14% round-trip.

    Leverage safety notes:
    - Designed for isolated futures leverage up to 3x.
    - Strategy edge assumes forced liquidation is never approached.
    """

    INTERFACE_VERSION = 3
    DEPLOYMENT_STAGE = "production_candidate"
    PRODUCTION_APPROVED = True
    can_short = True

    timeframe = "1m"
    informative_timeframe_1 = "3m"
    informative_timeframe_2 = "5m"

    startup_candle_count = 300
    process_only_new_candles = True

    # Dynamic ROI controls
    roi_t1 = IntParameter(6, 30, default=12, space="sell")
    roi_t2 = IntParameter(20, 70, default=35, space="sell")
    roi_p1 = DecimalParameter(0.0015, 0.0080, default=0.0035, decimals=4, space="sell")
    roi_p2 = DecimalParameter(0.0008, 0.0040, default=0.0018, decimals=4, space="sell")

    # Entry thresholds
    adx_min = IntParameter(16, 40, default=24, space="buy")
    ema_gap_min = DecimalParameter(0.0003, 0.0030, default=0.0012, decimals=4, space="buy")
    volume_mult = DecimalParameter(0.8, 2.5, default=1.2, decimals=2, space="buy")

    # Stoploss / trailing
    stoploss = -0.018
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True

    tsl_positive = DecimalParameter(0.003, 0.012, default=0.005, decimals=3, space="sell")
    tsl_offset = DecimalParameter(0.005, 0.018, default=0.008, decimals=3, space="sell")

    use_custom_stoploss = False

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_p1.value),
            str(int(self.roi_t1.value)): float(self.roi_p2.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 4,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 240,
                "trade_limit": 20,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.08,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe_1) for pair in pairs] + [
            (pair, self.informative_timeframe_2) for pair in pairs
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()

        inf3 = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe_1)
        inf3["ema_fast"] = ta.EMA(inf3, timeperiod=8)
        inf3["ema_slow"] = ta.EMA(inf3, timeperiod=21)
        inf3["adx"] = ta.ADX(inf3, timeperiod=14)

        inf5 = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe_2)
        inf5["ema_fast"] = ta.EMA(inf5, timeperiod=8)
        inf5["ema_slow"] = ta.EMA(inf5, timeperiod=21)

        dataframe = merge_informative_pair(dataframe, inf3, self.timeframe, self.informative_timeframe_1, ffill=True)
        dataframe = merge_informative_pair(dataframe, inf5, self.timeframe, self.informative_timeframe_2, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        gap = (dataframe["ema_fast"] - dataframe["ema_slow"]) / dataframe["close"]

        long_regime = (
            (dataframe["adx"] > self.adx_min.value)  # avoid chop
            & (dataframe["atr_pct"] > 0.0007)
            & (dataframe["adx_3m"] > self.adx_min.value)
            & (dataframe["ema_fast_5m"] > dataframe["ema_slow_5m"])
        )
        short_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["atr_pct"] > 0.0007)
            & (dataframe["adx_3m"] > self.adx_min.value)
            & (dataframe["ema_fast_5m"] < dataframe["ema_slow_5m"])
        )

        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * self.volume_mult.value

        dataframe.loc[
            long_regime & volume_ok & (gap > self.ema_gap_min.value) & (dataframe["close"] > dataframe["ema_fast"]),
            ["enter_long", "enter_tag"],
        ] = (1, "s1_microtrend_long")

        dataframe.loc[
            short_regime & volume_ok & (gap < -self.ema_gap_min.value) & (dataframe["close"] < dataframe["ema_fast"]),
            ["enter_short", "enter_tag"],
        ] = (1, "s1_microtrend_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema_fast"]) | (dataframe["adx"] < self.adx_min.value),
            ["exit_long", "exit_tag"],
        ] = (1, "s1_ema_loss")

        dataframe.loc[
            (dataframe["close"] > dataframe["ema_fast"]) | (dataframe["adx"] < self.adx_min.value),
            ["exit_short", "exit_tag"],
        ] = (1, "s1_ema_loss")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(3.0, max_leverage)

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        self.logger.info(
            {
                "event": "entry_confirm",
                "strategy": "S1",
                "pair": pair,
                "side": side,
                "entry_tag": entry_tag,
                "rate": rate,
                "timestamp": current_time.isoformat(),
            }
        )
        return True

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "exit_monitor",
                "strategy": "S1",
                "pair": pair,
                "side": trade.trade_direction,
                "profit": round(current_profit, 5),
                "open_minutes": int((current_time - trade.open_date_utc).total_seconds() / 60),
            }
        )
        return None
