import logging
import json

from typing import Dict
from pandas import DataFrame
from freqtrade.strategy.interface import IStrategy

import talib.abstract as ta

logger = logging.getLogger(__name__)


class FreqSignalsWebhookDataProvider(IStrategy):
        
    minimal_roi = {
        "0": 0.05
    }

    stoploss = -0.03
    timeframe = '5m'


    plot_config = {
        "main_plot": {},
        "subplots": {
            "RSI": {
                "rsi": {}
            },
        }
    }

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # Some logic to establish a signal. For simplicity, using RSI.
        df['rsi'] = ta.RSI(df, timeperiod=14)

        msg = json.dumps({
            # required fields
            "symbol": metadata['pair'],
            "value": round(df.iloc[-1]["rsi"], 4),
            "ttl_minutes": 60,
            "data_set_id": 'bcea098e-aca4-4bb7-b30e-060625342b22',
            # any additional context
            "rsi": round(df.iloc[-1]["rsi"], 4),
            "price": round(df.iloc[-1]["close"], 4),
            "last_move": round(df.iloc[-1]["close"] - df.iloc[-2]["close"], 4),
        })

        self.dp.send_msg(msg)

        return df

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["exit_long"] = 0
        return dataframe
