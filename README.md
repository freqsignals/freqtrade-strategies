# Freqtrade Strategies with Freqsignals

Implementation of sample Freqtrade Strategies that integrate with [FreqSignals.com](https://freqsignals.com).

## Installation and Use

The easiest way to integrate is to copy the contents of the `strategies` directory (or just `freqsignals.py` file) into your freqtrade's `userdata/strategies/` directory and then import it into your strategies. See [`strategies/FreqSignalsFollower.py`](strategies/FreqSignalsFollower.py) for an example freqtrade strategy that follows signals.

### Environment Variables

If you don't want to set environment variables, you can just set the variables `CLIENT_ID` and `CLIENT_SECRET` in the [`freqsignals.py`](strategies/freqsignals.py). If you can set environment variables, set `FREQSIGNALS_CLIENT_ID` and `FREQSIGNALS_CLIENT_SECRET` to the client id and secret you've generated in FreqSignals.

## Providing Signals

The easiest way to provide signals is to use Freqtrade's webhooks to send them and to call `self.dp.sent_msg(stringified_signal)` from within the strategy's `populate_indicators`.

Webhook Configuration:

    "webhook": {
        "enabled": true,
        "url": "https://api.freqsignals.com/api/async/freqtrade_webhook/?token=INTERGRATION_TOKEN",
        "retries": 3,
        "retry_delay": 0.2,
        "allow_custom_messages": true,
        "format": "json",
        "strategy_msg": {
            "data": "{msg}"
        }
    }

Strategy \`populate_indicators\`:

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # Some logic to establish a signal. For simplicity, using RSI.
        df['rsi'] = ta.RSI(df, timeperiod=14)

        msg = json.dumps({
            # required fields
            "symbol": metadata['pair'],
            "value": round(df.iloc[-1]["rsi"], 4),
            "ttl_minutes": 60,
            "data_set_id": "DATA_SET_ID",
            # any additional context fields
            "rsi": round(df.iloc[-1]["rsi"], 4),
            "price": round(df.iloc[-1]["close"], 4),
            "last_move": round(df.iloc[-1]["close"] - df.iloc[-2]["close"], 4),
        })

        self.dp.send_msg(msg)

        return df

See also:
- See the bottom of [`configs/config_binance_webhook.json`](configs/config_binance_webhook.json) for an example Webhook Configuration.
- See [`strategies/FreqSignalsWebhookDataProvider.py`](strategies/FreqSignalsWebhookDataProvider.py) for an example strategy.
- See [Documentation here](https://freqsignals.com/freqtrade_crypto_bot#documentation--upload-signals).


### Providing Signals without Webhooks

If you already have a webhook set up or don't want to use a webhook for some reason, you can manually send the Signal to FreqSignals leveraging [`freqsignals.py`](strategies/freqsignals.py). See [`strategies/FreqSignalsProvider.py`](strategies/FreqSignalsProvider.py) for a simple example of how to upload a signal using Freqtrade. This file assumes you have an `FREQSIGNALS_DATA_SET_ID` environment variable set, but it is implementation specific. You may configure a bot to upload to multiple data sets that you provide for.

Some Data Providers will use FreqAI and their powerful computers to generate their Signals that others can subscribe to. See or [`strategies/FreqSignalsAiDataProvider.py`](strategies/FreqSignalsAiDataProvider.py) example for how an integration with FreqAI could work.
