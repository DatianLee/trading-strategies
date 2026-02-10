from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter, merge_informative_pair


class S3_MFT_Conservative_TrendPullback(IStrategy):
    """
    S3: MFT Conservative Trend-Pullback (15m base, 1h regime).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.02% / side.
    - Cost baseline: ~0.12% round-trip.

    Leverage safety notes:
    - Conservative trend strategy, isolated leverage <= 3x.
    """

    INTERFACE_VERSION = 3
    DEPLOYMENT_STAGE = "production_candidate"
    PRODUCTION_APPROVED = True
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 300

    pullback_depth = DecimalParameter(0.002, 0.02, default=0.007, decimals=3, space="buy")
    adx_min = IntParameter(16, 40, default=24, space="buy")
    rsi_floor = IntParameter(30, 50, default=40, space="buy")
    rsi_ceiling = IntParameter(50, 70, default=60, space="buy")

    stoploss = -0.035
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    roi1 = DecimalParameter(0.01, 0.06, default=0.025, decimals=3, space="sell")
    roi2 = DecimalParameter(0.0, 0.03, default=0.008, decimals=3, space="sell")
    t1 = IntParameter(30, 180, default=90, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi1.value), str(int(self.t1.value)): float(self.roi2.value), "360": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 80,
                "trade_limit": 12,
                "stop_duration_candles": 12,
                "max_allowed_drawdown": 0.12,
            },
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 60,
                "trade_limit": 5,
                "stop_duration_candles": 20,
                "required_profit": 0.01,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)

        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        dataframe["pullback"] = (dataframe["ema20"] - dataframe["close"]) / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter for trend strategy: avoid chop via ADX + HTF trend alignment
        long_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["ema50_1h"] > dataframe["ema200_1h"])
        )
        short_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["ema50_1h"] < dataframe["ema200_1h"])
        )

        dataframe.loc[
            long_regime
            & (dataframe["pullback"] > self.pullback_depth.value)
            & (dataframe["rsi"] > self.rsi_floor.value),
            ["enter_long", "enter_tag"],
        ] = (1, "s3_pullback_long")

        dataframe.loc[
            short_regime
            & ((dataframe["close"] - dataframe["ema20"]) / dataframe["close"] > self.pullback_depth.value)
            & (dataframe["rsi"] < self.rsi_ceiling.value),
            ["enter_short", "enter_tag"],
        ] = (1, "s3_pullback_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema50"]) | (dataframe["rsi"] > 72), ["exit_long", "exit_tag"]] = (1, "s3_trend_break")
        dataframe.loc[(dataframe["close"] > dataframe["ema50"]) | (dataframe["rsi"] < 28), ["exit_short", "exit_tag"]] = (1, "s3_trend_break")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(3.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S3",
                "pair": pair,
                "entry_tag": trade.enter_tag,
                "direction": trade.trade_direction,
                "current_profit": round(current_profit, 5),
            }
        )
        return None
