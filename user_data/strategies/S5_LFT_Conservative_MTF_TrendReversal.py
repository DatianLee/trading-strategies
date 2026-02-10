from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S5_LFT_Conservative_MTF_TrendReversal(IStrategy):
    """
    S5: LFT Conservative Multi-Timeframe Trend-Reversal.

    Timeframes:
    - Base execution: 1h
    - Regime anchors: 4h and 1d

    Deterministic inputs:
    - OHLCV-only indicators.
    - Optional placeholders for funding/open-interest are provided as NaN columns.

    Capital protection state machine:
    - normal (state=0): full stake.
    - risk_off (state=1): reduced stake.
    - kill_switch (state=2): no new entries.
    """

    INTERFACE_VERSION = 3
    DEPLOYMENT_STAGE = "production_candidate"
    PRODUCTION_APPROVED = True
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    anchor_timeframe = "1d"
    startup_candle_count = 450

    adx_min = IntParameter(18, 38, default=24, space="buy")
    reversal_rsi_long = IntParameter(30, 48, default=40, space="buy")
    reversal_rsi_short = IntParameter(52, 70, default=60, space="buy")
    volatility_ceiling = DecimalParameter(0.01, 0.08, default=0.035, decimals=3, space="buy")

    stoploss = -0.05
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.035, "240": 0.015, "720": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 4,
                "stop_duration_candles": 30,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 200,
                "trade_limit": 16,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.11,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative = [(pair, self.informative_timeframe) for pair in pairs]
        informative.extend((pair, self.anchor_timeframe) for pair in pairs)
        return informative

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        # Higher values indicate stressed market conditions.
        dataframe["stress_score"] = (
            (dataframe["atr_pct"] > dataframe["atr_pct"].rolling(120).quantile(0.85)).astype(int)
            + (dataframe["volume"] > 1.8 * dataframe["volume"].rolling(48).mean()).astype(int)
            + (dataframe["close"] < dataframe["ema200"]).astype(int)
        )

        dataframe["capital_state"] = 0
        dataframe.loc[dataframe["stress_score"] >= 2, "capital_state"] = 1
        dataframe.loc[
            (dataframe["stress_score"] >= 3)
            | ((dataframe["close"] / dataframe["close"].shift(24) - 1) < -0.08),
            "capital_state",
        ] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        inf_4h = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf_4h["ema50"] = ta.EMA(inf_4h, timeperiod=50)
        inf_4h["ema200"] = ta.EMA(inf_4h, timeperiod=200)
        inf_4h["adx"] = ta.ADX(inf_4h, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf_4h, self.timeframe, self.informative_timeframe, ffill=True)

        inf_1d = self.dp.get_pair_dataframe(metadata["pair"], self.anchor_timeframe)
        inf_1d["ema50"] = ta.EMA(inf_1d, timeperiod=50)
        inf_1d["ema200"] = ta.EMA(inf_1d, timeperiod=200)
        inf_1d["rsi"] = ta.RSI(inf_1d, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf_1d, self.timeframe, self.anchor_timeframe, ffill=True)

        # Optional placeholders for exchange-specific derivatives data.
        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: low trend strength, unstable volatility, and kill-switch state.
        notrade_filter = (
            (dataframe["adx"] < self.adx_min.value)
            | (dataframe["atr_pct"] > self.volatility_ceiling.value)
            | (dataframe["volume"] < 0.6 * dataframe["volume"].rolling(48).mean())
            | (dataframe["capital_state"] >= 2)
        )

        long_reversal = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] > dataframe["ema200_1d"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] > self.reversal_rsi_long.value)
            & (dataframe["rsi"].shift(1) < self.reversal_rsi_long.value)
            & (dataframe["rsi_1d"] > 45)
        )

        short_reversal = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] < dataframe["ema200_1d"])
            & (dataframe["close"] < dataframe["ema50"])
            & (dataframe["rsi"] < self.reversal_rsi_short.value)
            & (dataframe["rsi"].shift(1) > self.reversal_rsi_short.value)
            & (dataframe["rsi_1d"] < 55)
        )

        dataframe.loc[long_reversal & ~notrade_filter, ["enter_long", "enter_tag"]] = (1, "s5_mtf_rev_long")
        dataframe.loc[short_reversal & ~notrade_filter, ["enter_short", "enter_tag"]] = (1, "s5_mtf_rev_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema50"]) | (dataframe["rsi"] > 75) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s5_regime_or_risk")
        dataframe.loc[
            (dataframe["close"] > dataframe["ema50"]) | (dataframe["rsi"] < 25) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s5_regime_or_risk")
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        return self._latest_capital_state(pair) < 2

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float, leverage: float, entry_tag: str | None,
                            side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state >= 2:
            return 0.0
        if state == 1:
            return proposed_stake * 0.4
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.5, max_leverage)
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s5_kill_switch_exit"
        return None
