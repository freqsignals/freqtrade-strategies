import os
import logging

from typing import Dict
from pandas import DataFrame
from freqsignals import FreqSignalsStrategy, FreqSignalsMixin
from freqtrade.strategy.interface import IStrategy

import talib.abstract as ta
DATA_SET_ID = os.environ.get("FREQSIGNALS_DATA_SET_ID")

logger = logging.getLogger(__name__)


class FreqSignalsProvider(IStrategy, FreqSignalsMixin):
        
    minimal_roi = {
        "0": 0.05
    }

    stoploss = -0.03
    timeframe = '1m'


    plot_config = {
        "main_plot": {},
        "subplots": {
            "RSI": {
                "rsi": {}
            },
            "Signal": {
                "signal": {}
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.freqsignals_init()
        self.signal_update_time_by_pair: Dict[str, str] = {}


    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # Some logic to establish a signal
        df['rsi'] = ta.RSI(df, timeperiod=14)

        df.loc[(
            (df['rsi'] >= 55) &
            (df['volume'] > 0)
        ),
        'signal'] = 0.05

        df.loc[(
            (df['rsi'] <= 45) &
            (df['volume'] > 0)
        ),
        'signal'] = -0.05

        signal = df.iloc[-1]['signal']
        last_update_time = self.signal_update_time_by_pair.get(metadata['pair'])
        current_candle_time = df.iloc[-1].date

        if ((signal > 0 or signal < 0) and (last_update_time is None or last_update_time != current_candle_time)):
            # If there's a move, upload the signal with time TTL (minutes)
            self.signal_update_time_by_pair[metadata['pair']] = current_candle_time
            logger.info(f"setting signal for {metadata['pair']} to {signal} at {current_candle_time}")
            self.freqsignals_client.post_signal({
                # required fields
                "symbol": metadata['pair'],
                "value": signal,
                "ttl_minutes": 60,
                "data_set_id": DATA_SET_ID,
                # any additional context
                "rsi": df.iloc[-1]["rsi"],
            })

        return df

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Not making any trades, just submitting signals
        dataframe["exit_long"] = 0
        return dataframe
