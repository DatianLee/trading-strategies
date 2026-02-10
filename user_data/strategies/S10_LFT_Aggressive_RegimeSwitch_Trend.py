from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S10_LFT_Aggressive_RegimeSwitch_Trend(IStrategy):
    """
    S10: LFT Aggressive Regime-Switch Trend (1h base, 4h+1d filters).
    """

    INTERFACE_VERSION = 3
    DEPLOYMENT_STAGE = "experimental"
    PRODUCTION_APPROVED = False
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    anchor_timeframe = "1d"
    startup_candle_count = 500

    adx_floor = IntParameter(18, 40, default=26, space="buy")
    breakout_buffer = DecimalParameter(0.002, 0.03, default=0.008, decimals=3, space="buy")
    atr_cap = DecimalParameter(0.02, 0.10, default=0.06, decimals=3, space="buy")

    stoploss = -0.065
    trailing_stop = True
    trailing_stop_positive = 0.018
    trailing_stop_positive_offset = 0.038
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.020, 0.080, default=0.038, decimals=3, space="sell")
    roi_mid = DecimalParameter(0.006, 0.040, default=0.016, decimals=3, space="sell")
    roi_t1 = IntParameter(18, 120, default=48, space="sell")
    roi_t2 = IntParameter(72, 360, default=168, space="sell")

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
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 100,
                "trade_limit": 5,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 220,
                "trade_limit": 18,
                "stop_duration_candles": 32,
                "max_allowed_drawdown": 0.16,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(p, self.informative_timeframe) for p in pairs] + [(p, self.anchor_timeframe) for p in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["high_48"] = dataframe["high"].rolling(48).max()
        dataframe["low_48"] = dataframe["low"].rolling(48).min()

        inf4h = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf4h["ema50"] = ta.EMA(inf4h, timeperiod=50)
        inf4h["ema200"] = ta.EMA(inf4h, timeperiod=200)
        inf4h["adx"] = ta.ADX(inf4h, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf4h, self.timeframe, self.informative_timeframe, ffill=True)

        inf1d = self.dp.get_pair_dataframe(metadata["pair"], self.anchor_timeframe)
        inf1d["ema50"] = ta.EMA(inf1d, timeperiod=50)
        inf1d["ema200"] = ta.EMA(inf1d, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, inf1d, self.timeframe, self.anchor_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volatile_but_tradeable = (dataframe["atr_pct"] > 0.008) & (dataframe["atr_pct"] < self.atr_cap.value)
        trend_gate_long = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] > dataframe["ema200_1d"])
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["adx_4h"] > self.adx_floor.value)
        )
        trend_gate_short = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] < dataframe["ema200_1d"])
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["adx_4h"] > self.adx_floor.value)
        )

        dataframe.loc[
            trend_gate_long
            & volatile_but_tradeable
            & (dataframe["close"] > dataframe["high_48"].shift(1) * (1 + self.breakout_buffer.value)),
            ["enter_long", "enter_tag"],
        ] = (1, "s10_breakout_long")

        dataframe.loc[
            trend_gate_short
            & volatile_but_tradeable
            & (dataframe["close"] < dataframe["low_48"].shift(1) * (1 - self.breakout_buffer.value)),
            ["enter_short", "enter_tag"],
        ] = (1, "s10_breakout_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema50"]) | (dataframe["adx"] < self.adx_floor.value), ["exit_long", "exit_tag"]] = (1, "s10_trend_fail")
        dataframe.loc[(dataframe["close"] > dataframe["ema50"]) | (dataframe["adx"] < self.adx_floor.value), ["exit_short", "exit_tag"]] = (1, "s10_trend_fail")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.2, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.04 and (current_time - trade.open_date_utc).total_seconds() > 24 * 3600:
            return "s10_stale_loss"
        return None
