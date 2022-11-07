# Freqtrade Strategies with Freqsignals

Implementation of sample Freqtrade Strategies that integrate with [FreqSignals.com](https://freqsignals.com).

## Installation and use

The easiest way to integrate is to copy the contents of the `strategies` directory (or just `freqsignals.py` file) into your freqtrade's `userdata/strategies/` directory and then import it into your strategies. See `strategies/Follower.py` for an example freqtrade strategy that uses the signals.

### Environment Variables

If you don't want to set environment variables, you can just set the variables `CLIENT_ID` and `CLIENT_SECRET` in the `freqsignals.py`. If you can set environment variables, set `FREQSIGNALS_CLIENT_ID` and `FREQSIGNALS_CLIENT_SECRET` to the client id and secret you've generated in FreqSignals.

## Providing Signals

If you have been set up as a FreqSignals Data Provider and have a data set, see `strategies/Provider.py` for a simple example of how to upload a signal using Freqtrade. This file assumes you have an `FREQSIGNALS_DATA_SET_ID` environment variable set, but it is implementation specific. You may configure a bot to upload to multiple data sets that you provide for.