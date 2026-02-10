from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S8_HFT_Progressive_Orderflow_Impulse(IStrategy):
    """
    S8: HFT Progressive Orderflow Impulse (1m + 5m context).
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1m"
    informative_timeframe = "5m"
    startup_candle_count = 320

    adx_floor = IntParameter(14, 36, default=20, space="buy")
    impulse_threshold = DecimalParameter(0.0008, 0.0060, default=0.0022, decimals=4, space="buy")
    volume_spike_mult = DecimalParameter(1.1, 3.0, default=1.6, decimals=2, space="buy")

    stoploss = -0.024
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.010
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.003, 0.014, default=0.006, decimals=3, space="sell")
    roi_slow = DecimalParameter(0.0, 0.007, default=0.002, decimals=3, space="sell")
    roi_t1 = IntParameter(4, 22, default=10, space="sell")
    roi_t2 = IntParameter(16, 64, default=28, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_fast.value),
            str(int(self.roi_t1.value)): float(self.roi_slow.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 5,
                "stop_duration_candles": 16,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 220,
                "trade_limit": 24,
                "stop_duration_candles": 28,
                "max_allowed_drawdown": 0.1,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        dataframe["impulse"] = (dataframe["close"] - dataframe["open"]) / dataframe["open"]

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema21"] = ta.EMA(inf, timeperiod=21)
        inf["ema55"] = ta.EMA(inf, timeperiod=55)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * self.volume_spike_mult.value
        trend_long = (dataframe["ema21_5m"] > dataframe["ema55_5m"]) & (dataframe["adx_5m"] > self.adx_floor.value)
        trend_short = (dataframe["ema21_5m"] < dataframe["ema55_5m"]) & (dataframe["adx_5m"] > self.adx_floor.value)

        dataframe.loc[
            trend_long
            & volume_ok
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["impulse"] > self.impulse_threshold.value)
            & (dataframe["atr_pct"] > 0.0008),
            ["enter_long", "enter_tag"],
        ] = (1, "s8_impulse_long")

        dataframe.loc[
            trend_short
            & volume_ok
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["impulse"] < -self.impulse_threshold.value)
            & (dataframe["atr_pct"] > 0.0008),
            ["enter_short", "enter_tag"],
        ] = (1, "s8_impulse_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema9"]), ["exit_long", "exit_tag"]] = (1, "s8_momentum_fade")
        dataframe.loc[(dataframe["close"] > dataframe["ema9"]), ["exit_short", "exit_tag"]] = (1, "s8_momentum_fade")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.5, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.015 and (current_time - trade.open_date_utc).total_seconds() > 25 * 60:
            return "s8_time_stop"
        return None
