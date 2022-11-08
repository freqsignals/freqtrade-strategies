from pandas import DataFrame
from freqsignals import FreqSignalsStrategy


class FreqSignalsFollower(FreqSignalsStrategy):

    freqsignals_data_set_names = {
        # Mapping of a data set id to the name of the feature / column
        "e7041595-8851-4c80-aba5-944468ee7820": "fs_signal"
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
                "fs_signal": {}
            }
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.freqsignals_add_pair_signals(dataframe, metadata['pair'])

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
