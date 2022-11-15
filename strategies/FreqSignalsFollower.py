import os
from pandas import DataFrame
from freqsignals import FreqSignalsStrategy
DATA_SET_ID = os.environ.get("FREQSIGNALS_DATA_SET_ID")


class FreqSignalsFollower(FreqSignalsStrategy):

    freqsignals_data_set_names = {
        # Mapping of a data set id to the name of the feature / column
        DATA_SET_ID: "fs_signal"
    }

    minimal_roi = {
        "0": 0.05
    }

    stoploss = -0.03
    timeframe = '1m'

    plot_config = {
        "main_plot": {},
        "subplots": {
            "Signals": {
                "fs_signal": {},
                "fs_signal_last_move": {}
            }
        }
    }


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Set a default for if it's not found
        dataframe['fs_signal'] = None

        self.freqsignals_load_signal_history(metadata['pair'], DATA_SET_ID)
        dataframe = self.freqsignals_add_pair_signals(dataframe, metadata['pair'], include_context=True)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        dataframe.loc[(
            (dataframe['fs_signal'] >= 0.01) &
            (dataframe['volume'] > 0)
        ),
        ['enter_long', 'enter_tag']] = (1, 'bullish_signal')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(
            (dataframe['fs_signal'] <= -0.01) &
            (dataframe['volume'] > 0)
        ),
        ['exit_long', 'exit_tag']] = (1, 'bearish_signal')
        return dataframe
