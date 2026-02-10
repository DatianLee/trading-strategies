from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class S7_Event_Volatility_Shock_Strategy(IStrategy):
    """
    S7: Event/Volatility Shock Strategy.

    Deterministic event proxies (OHLCV-only):
    1) volatility burst
    2) volume spike
    3) range expansion + follow-through

    No external news API is used.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 350

    stoploss = -0.04
    trailing_stop = True
    trailing_stop_positive = 0.014
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.03, "90": 0.012, "360": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 8},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 5,
                "stop_duration_candles": 36,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 140,
                "trade_limit": 16,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.12,
            },
        ]

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        recent_drop = dataframe["close"] / dataframe["close"].shift(32) - 1
        stress = (dataframe["volatility_burst"] & dataframe["volume_spike"]).astype(int) + (recent_drop < -0.07).astype(int)
        dataframe["capital_state"] = 0
        dataframe.loc[stress >= 1, "capital_state"] = 1
        dataframe.loc[(stress >= 2) | (recent_drop < -0.12), "capital_state"] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        dataframe["volatility_burst"] = dataframe["atr_pct"] > dataframe["atr_pct"].rolling(96).quantile(0.9)
        dataframe["volume_spike"] = dataframe["volume"] > dataframe["volume"].rolling(96).mean() * 2.0

        dataframe["true_range"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["range_expansion"] = dataframe["true_range"] > dataframe["true_range"].rolling(96).quantile(0.9)

        # Follow-through uses the already closed previous candle to avoid lookahead.
        dataframe["bull_follow_through"] = dataframe["close"].shift(1) > dataframe["high"].shift(2)
        dataframe["bear_follow_through"] = dataframe["close"].shift(1) < dataframe["low"].shift(2)

        dataframe["event_proxy_long"] = (
            dataframe["volatility_burst"] & dataframe["volume_spike"] & dataframe["range_expansion"] & dataframe["bull_follow_through"]
        )
        dataframe["event_proxy_short"] = (
            dataframe["volatility_burst"] & dataframe["volume_spike"] & dataframe["range_expansion"] & dataframe["bear_follow_through"]
        )

        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: no event confirmation, post-shock chop, or kill-switch mode.
        avoid_trading = (
            (dataframe["capital_state"] >= 2)
            | (dataframe["volume"] < dataframe["volume"].rolling(48).mean() * 0.8)
            | (dataframe["atr_pct"] < dataframe["atr_pct"].rolling(96).quantile(0.4))
        )

        dataframe.loc[
            dataframe["event_proxy_long"] & (dataframe["close"] > dataframe["ema20"]) & ~avoid_trading,
            ["enter_long", "enter_tag"],
        ] = (1, "s7_event_long")

        dataframe.loc[
            dataframe["event_proxy_short"] & (dataframe["close"] < dataframe["ema20"]) & ~avoid_trading,
            ["enter_short", "enter_tag"],
        ] = (1, "s7_event_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema20"]) | (dataframe["rsi"] > 74) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s7_post_event_exit")

        dataframe.loc[
            (dataframe["close"] > dataframe["ema20"]) | (dataframe["rsi"] < 26) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s7_post_event_exit")
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
            return proposed_stake * 0.35
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.4, max_leverage)
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s7_kill_switch_exit"
        return None
