from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter, merge_informative_pair


class S4_MFT_Progressive_BreakoutRetest(IStrategy):
    """
    S4: MFT Progressive Breakout-Retest (15m base, 1h context).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.03% / side near breakout spikes.
    - Cost baseline: ~0.14% round-trip.

    Leverage safety notes:
    - Allow isolated leverage <= 2.5x due to breakout failure risk.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 350

    breakout_window = IntParameter(20, 100, default=55, space="buy")
    retest_buffer = DecimalParameter(0.0005, 0.008, default=0.002, decimals=4, space="buy")
    adx_min = IntParameter(16, 45, default=26, space="buy")

    stoploss = -0.03
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    roi_initial = DecimalParameter(0.01, 0.08, default=0.03, decimals=3, space="sell")
    roi_decay = DecimalParameter(0.0, 0.03, default=0.01, decimals=3, space="sell")
    roi_t = IntParameter(40, 220, default=120, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi_initial.value), str(int(self.roi_t.value)): float(self.roi_decay.value), "600": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 100,
                "trade_limit": 4,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 120,
                "trade_limit": 15,
                "stop_duration_candles": 24,
                "max_allowed_drawdown": 0.10,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["hh"] = dataframe["high"].rolling(int(self.breakout_window.value)).max()
        dataframe["ll"] = dataframe["low"].rolling(int(self.breakout_window.value)).min()

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter: avoid chop for breakout systems.
        trend_ok = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["atr_pct"] > 0.001)
        )

        long_break = dataframe["close"] > dataframe["hh"].shift(1)
        long_retest = (dataframe["close"] <= dataframe["hh"].shift(1) * (1 + self.retest_buffer.value)) & (
            dataframe["close"] >= dataframe["hh"].shift(1) * (1 - self.retest_buffer.value)
        )

        short_break = dataframe["close"] < dataframe["ll"].shift(1)
        short_retest = (dataframe["close"] >= dataframe["ll"].shift(1) * (1 - self.retest_buffer.value)) & (
            dataframe["close"] <= dataframe["ll"].shift(1) * (1 + self.retest_buffer.value)
        )

        dataframe.loc[
            trend_ok & (dataframe["ema50_1h"] > dataframe["ema200_1h"]) & long_break & long_retest,
            ["enter_long", "enter_tag"],
        ] = (1, "s4_breakout_long")

        dataframe.loc[
            trend_ok & (dataframe["ema50_1h"] < dataframe["ema200_1h"]) & short_break & short_retest,
            ["enter_short", "enter_tag"],
        ] = (1, "s4_breakout_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["hh"].shift(1)) | (dataframe["adx"] < 15), ["exit_long", "exit_tag"]] = (1, "s4_failed_break")
        dataframe.loc[(dataframe["close"] > dataframe["ll"].shift(1)) | (dataframe["adx"] < 15), ["exit_short", "exit_tag"]] = (1, "s4_failed_break")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.5, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S4",
                "pair": pair,
                "side": trade.trade_direction,
                "entry_tag": trade.enter_tag,
                "profit": round(current_profit, 5),
            }
        )
        return None
