from pandas import DataFrame
from freqsignals import FreqSignalsStrategy


class FreqSignalsFollower(FreqSignalsStrategy):

    minimal_roi = {
        "0": 0.05
    }

    stoploss = -0.03
    timeframe = '1m'

    plot_config = {
        "main_plot": {},
        "subplots": {
            "Signals": {
                "signal": {}
            }
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.freqsignals_add_pair_signals(dataframe, metadata['pair'])

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        dataframe.loc[(
            (dataframe['signal'] >= 0.01) &
            (dataframe['volume'] > 0)
        ),
        ['enter_long', 'enter_tag']] = (1, 'bullish signal')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(
            (dataframe['signal'] <= -0.01) &
            (dataframe['volume'] > 0)
        ),
        ['exit_long', 'exit_tag']] = (1, 'bearish signal')
        return dataframe
