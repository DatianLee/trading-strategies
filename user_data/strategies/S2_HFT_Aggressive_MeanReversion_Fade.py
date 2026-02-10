from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter


class S2_HFT_Aggressive_MeanReversion_Fade(IStrategy):
    """
    S2: HFT Aggressive Mean-Reversion Fade (1m base, 5m context).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.05% / side (aggressive entries).
    - Combined cost baseline: ~0.18% round-trip.

    Leverage safety notes:
    - Keep isolated leverage <= 2x because fades can stack into trend legs.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1m"
    startup_candle_count = 250

    zscore_threshold = DecimalParameter(1.2, 3.5, default=2.1, decimals=2, space="buy")
    rsi_low = IntParameter(10, 40, default=24, space="buy")
    rsi_high = IntParameter(60, 90, default=76, space="buy")
    adx_max = IntParameter(14, 30, default=22, space="buy")

    stoploss = -0.022
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.009
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.002, 0.012, default=0.005, decimals=3, space="sell")
    roi_slow = DecimalParameter(0.0, 0.006, default=0.001, decimals=3, space="sell")
    roi_t = IntParameter(4, 25, default=10, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi_fast.value), str(int(self.roi_t.value)): float(self.roi_slow.value)}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 10},
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 100,
                "trade_limit": 6,
                "stop_duration_candles": 20,
                "required_profit": 0.005,
            },
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 180,
                "trade_limit": 5,
                "stop_duration_candles": 30,
                "only_per_pair": False,
            },
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["std"] = dataframe["close"].rolling(50).std()
        dataframe["zscore"] = (dataframe["close"] - dataframe["ema"]) / dataframe["std"]
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["ema_slope"] = dataframe["ema"].pct_change(5)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter: avoid one-way trends for mean-reversion
        mr_regime = (dataframe["adx"] < self.adx_max.value) & (dataframe["ema_slope"].abs() < 0.0035)

        dataframe.loc[
            mr_regime
            & (dataframe["zscore"] < -self.zscore_threshold.value)
            & (dataframe["rsi"] < self.rsi_low.value),
            ["enter_long", "enter_tag"],
        ] = (1, "s2_fade_long")

        dataframe.loc[
            mr_regime
            & (dataframe["zscore"] > self.zscore_threshold.value)
            & (dataframe["rsi"] > self.rsi_high.value),
            ["enter_short", "enter_tag"],
        ] = (1, "s2_fade_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["zscore"] > -0.2) | (dataframe["rsi"] > 50), ["exit_long", "exit_tag"]] = (1, "s2_revert")
        dataframe.loc[(dataframe["zscore"] < 0.2) | (dataframe["rsi"] < 50), ["exit_short", "exit_tag"]] = (1, "s2_revert")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S2",
                "pair": pair,
                "direction": trade.trade_direction,
                "entry_tag": trade.enter_tag,
                "pnl": round(current_profit, 5),
                "duration_min": int((current_time - trade.open_date_utc).total_seconds() / 60),
            }
        )
        return None
