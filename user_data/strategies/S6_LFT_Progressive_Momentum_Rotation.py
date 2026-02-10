from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S6_LFT_Progressive_Momentum_Rotation(IStrategy):
    """
    S6: LFT Progressive Momentum Rotation.

    Relative-strength anchor set:
    - BTC/USDT:USDT
    - ETH/USDT:USDT
    - SOL/USDT:USDT

    Strategy adapts benchmark momentum to pair-level signals by comparing
    pair return and trend quality versus benchmark basket return.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    startup_candle_count = 450

    momentum_window = IntParameter(12, 72, default=24, space="buy")
    rs_threshold = DecimalParameter(0.002, 0.08, default=0.015, decimals=3, space="buy")
    adx_min = IntParameter(16, 40, default=22, space="buy")

    stoploss = -0.055
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True

    benchmark_pairs = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.04, "180": 0.018, "600": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 96,
                "trade_limit": 5,
                "stop_duration_candles": 24,
                "only_per_pair": False,
            },
        ]

    def informative_pairs(self):
        pairs = set(self.dp.current_whitelist())
        pairs.update(self.benchmark_pairs)
        return [(pair, self.informative_timeframe) for pair in pairs]

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        drawdown_48h = dataframe["close"] / dataframe["close"].rolling(48).max() - 1
        dataframe["capital_state"] = 0
        risk_off = (drawdown_48h < -0.06) | (dataframe["atr_pct"] > dataframe["atr_pct"].rolling(96).quantile(0.9))
        kill_switch = (drawdown_48h < -0.1) & (dataframe["volume"] > 2.2 * dataframe["volume"].rolling(48).mean())
        dataframe.loc[risk_off, "capital_state"] = 1
        dataframe.loc[kill_switch, "capital_state"] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def _benchmark_return(self, pair: str, window: int) -> float:
        if not self.dp:
            return 0.0
        informative, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if informative is None or informative.empty or len(informative) <= window:
            return 0.0
        return float(informative["close"].iloc[-1] / informative["close"].iloc[-window] - 1)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["pair_ret"] = dataframe["close"].pct_change(int(self.momentum_window.value))

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)

        benchmark_returns = []
        window = int(self.momentum_window.value)
        for bench in self.benchmark_pairs:
            bench_df = self.dp.get_pair_dataframe(bench, self.timeframe)
            if bench_df is not None and len(bench_df) > window:
                benchmark_returns.append(bench_df["close"].pct_change(window))

        if benchmark_returns:
            bench_mean_series = sum(benchmark_returns) / len(benchmark_returns)
            aligned = bench_mean_series.reindex(dataframe.index).ffill()
            dataframe["benchmark_ret"] = aligned
        else:
            dataframe["benchmark_ret"] = 0.0

        dataframe["rs_score"] = dataframe["pair_ret"] - dataframe["benchmark_ret"]
        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: weak trend quality, insufficient liquidity, and kill-switch risk.
        avoid_trading = (
            (dataframe["adx"] < self.adx_min.value)
            | (dataframe["volume"] < dataframe["volume"].rolling(48).mean() * 0.7)
            | (dataframe["atr_pct"] > 0.07)
            | (dataframe["capital_state"] >= 2)
        )

        long_signal = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["close"] > dataframe["ema20"])
            & (dataframe["rs_score"] > self.rs_threshold.value)
            & (dataframe["rs_score"] > dataframe["rs_score"].shift(1))
        )

        short_signal = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["close"] < dataframe["ema20"])
            & (dataframe["rs_score"] < -self.rs_threshold.value)
            & (dataframe["rs_score"] < dataframe["rs_score"].shift(1))
        )

        dataframe.loc[long_signal & ~avoid_trading, ["enter_long", "enter_tag"]] = (1, "s6_rotation_long")
        dataframe.loc[short_signal & ~avoid_trading, ["enter_short", "enter_tag"]] = (1, "s6_rotation_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rs_score"] < 0) | (dataframe["close"] < dataframe["ema20"]) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s6_rs_decay")
        dataframe.loc[
            (dataframe["rs_score"] > 0) | (dataframe["close"] > dataframe["ema20"]) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s6_rs_decay")
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
            return proposed_stake * 0.5
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.8, max_leverage)
        return min(2.3, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s6_kill_switch_exit"
        return None
