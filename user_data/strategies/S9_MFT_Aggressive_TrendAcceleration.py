from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S9_MFT_Aggressive_TrendAcceleration(IStrategy):
    """
    S9: MFT Aggressive Trend Acceleration (15m + 1h context).
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 350

    adx_floor = IntParameter(16, 38, default=24, space="buy")
    roc_threshold = DecimalParameter(0.004, 0.03, default=0.012, decimals=3, space="buy")
    atr_floor = DecimalParameter(0.003, 0.03, default=0.009, decimals=3, space="buy")

    stoploss = -0.042
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.010, 0.050, default=0.021, decimals=3, space="sell")
    roi_mid = DecimalParameter(0.003, 0.025, default=0.010, decimals=3, space="sell")
    roi_t1 = IntParameter(12, 72, default=24, space="sell")
    roi_t2 = IntParameter(40, 180, default=90, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_fast.value),
            str(int(self.roi_t1.value)): float(self.roi_mid.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 3},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 96,
                "trade_limit": 6,
                "stop_duration_candles": 18,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 180,
                "trade_limit": 20,
                "stop_duration_candles": 24,
                "max_allowed_drawdown": 0.14,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=6) / 100
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        strong_market = (dataframe["atr_pct"] > self.atr_floor.value) & (dataframe["adx"] > self.adx_floor.value)
        long_bias = (dataframe["ema50_1h"] > dataframe["ema200_1h"]) & (dataframe["adx_1h"] > self.adx_floor.value)
        short_bias = (dataframe["ema50_1h"] < dataframe["ema200_1h"]) & (dataframe["adx_1h"] > self.adx_floor.value)

        dataframe.loc[
            strong_market
            & long_bias
            & (dataframe["close"] > dataframe["ema20"])
            & (dataframe["roc"] > self.roc_threshold.value)
            & (dataframe["rsi"] > 53),
            ["enter_long", "enter_tag"],
        ] = (1, "s9_accel_long")

        dataframe.loc[
            strong_market
            & short_bias
            & (dataframe["close"] < dataframe["ema20"])
            & (dataframe["roc"] < -self.roc_threshold.value)
            & (dataframe["rsi"] < 47),
            ["enter_short", "enter_tag"],
        ] = (1, "s9_accel_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema20"]) | (dataframe["roc"] < 0), ["exit_long", "exit_tag"]] = (1, "s9_decel")
        dataframe.loc[(dataframe["close"] > dataframe["ema20"]) | (dataframe["roc"] > 0), ["exit_short", "exit_tag"]] = (1, "s9_decel")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.8, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.03 and (current_time - trade.open_date_utc).total_seconds() > 8 * 3600:
            return "s9_timeout_loss"
        return None
