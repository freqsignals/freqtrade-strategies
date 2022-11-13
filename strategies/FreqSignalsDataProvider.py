import os
import logging

from typing import Dict
from pandas import DataFrame
from freqsignals import FreqSignalsStrategy, FreqSignalsMixin
from freqtrade.strategy.interface import IStrategy

import talib.abstract as ta
DATA_SET_ID = os.environ.get("FREQSIGNALS_DATA_SET_ID")

logger = logging.getLogger(__name__)


class FreqSignalsDataProvider(IStrategy, FreqSignalsMixin):
        
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.freqsignals_init()
        self.signal_update_time_by_pair: Dict[str, str] = {}


    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # Some logic to establish a signal
        df['rsi'] = ta.RSI(df, timeperiod=14)
        df['overbought'] = 0
        df['oversold'] = 0

        df.loc[(
            (df['rsi'] >= 70) &
            (df['volume'] > 0)
        ),
        'overbought'] = 1

        df.loc[(
            (df['rsi'] <= 30) &
            (df['volume'] > 0)
        ),
        'oversold'] = 1

        last_update_time = self.signal_update_time_by_pair.get(metadata['pair'])
        current_candle_time = df.iloc[-1].date

        if (last_update_time is None or last_update_time != current_candle_time):
            # If there's a move, upload the signal with time TTL (minutes)
            self.signal_update_time_by_pair[metadata['pair']] = current_candle_time
            signal_data = {
                # required fields
                "symbol": metadata['pair'],
                "value": round(df.iloc[-1]["close"] - df.iloc[-2]["close"], 4),
                "ttl_minutes": 60,
                "data_set_id": DATA_SET_ID,
                # any additional context
                "rsi": round(df.iloc[-1]["rsi"], 2),
                "overbought": int(df.iloc[-1]["overbought"]),
                "oversold": int(df.iloc[-1]["oversold"]),
                "price": round(df.iloc[-1]["close"], 4),
                "last_move": round(df.iloc[-1]["close"] - df.iloc[-2]["close"], 4),
            }
            logger.info(f"setting signal for {metadata['pair']} at {current_candle_time}")
            # logger.info(signal_data)
            # import pdb
            # pdb.set_trace()
            self.freqsignals_client.post_signal(signal_data)

        return df

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["exit_long"] = 0
        return dataframe
