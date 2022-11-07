import os
import logging
import requests
from urllib.parse import urlencode
from freqtrade.strategy.interface import IStrategy
from typing import Dict, Tuple
from pandas import DataFrame
from datetime import datetime, timedelta


import time
from requests.exceptions import ConnectTimeout, RequestException


class FreqSignalsError(Exception):
    pass


class FreqSignalsTimeoutError(Exception):
    pass



DEFAULT_HOST = os.environ.get("FREQSIGNALS_HOST", "api.freqsignals.com")
DEFAULT_HTTPS = str(os.environ.get("FREQSIGNALS_HTTPS", "1")) != "0"
DEFAULT_CLIENT_ID = os.environ.get("FREQSIGNALS_CLIENT_ID")
DEFAULT_CLIENT_SECRET = os.environ.get("FREQSIGNALS_CLIENT_SECRET")
DEFAULT_REQUEST_TIMEOUT = 20
DEFAULT_REQUEST_MAX_ATTEMPTS = 2
DEFAULT_REQUEST_WAIT_INTERVAL = 1


class FreqSignalsClient:
    def __init__(
        self,
        client_id=DEFAULT_CLIENT_ID,
        client_secret=DEFAULT_CLIENT_SECRET,
        host=DEFAULT_HOST,
        https=DEFAULT_HTTPS,
        request_timeout=DEFAULT_REQUEST_TIMEOUT,
        request_max_attempts=DEFAULT_REQUEST_MAX_ATTEMPTS,
        request_wait_interval=DEFAULT_REQUEST_WAIT_INTERVAL,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host
        self._https = https
        self._request_timeout = request_timeout
        self._request_max_attempts = request_max_attempts
        self._request_wait_interval = request_wait_interval
        self._token = None

    def get_token(self):
        if self._token is None:
            post_data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
            protocol_string = "https" if self._https else "http"
            url = f"{protocol_string}://{self._host}/oa2/token/"

            response = requests.post(url, json=post_data, verify=self._https)

            assert response.status_code == 200, response.json()
            res_data = response.json()
            assert "access_token" in res_data, res_data
            assert "expires_in" in res_data, res_data
            assert "scope" in res_data, res_data
            assert "token_type" in res_data, res_data

            self._token = res_data["access_token"]
        return self._token

    def get_headers(self):
        return {"Authorization": f"Bearer {self.get_token()}"}

    def get_full_url(self, url):
        protocol_string = "https" if self._https else "http"
        return f"{protocol_string}://{self._host}{url}"

    def make_request(self, url, method="get", data=None, headers=None, remaining_attempts=1):
        """
        Issues the request to FreqSignals
        Args:
            url: str - path to request
            method: str - get | post
            data: dict - optional - body of the post
            headers: dict - optional - headers to include
            remaining_attempts: how many more requests to make

        Returns:
            list - results or raises FreqSignalsError
        """
        data_response = None
        while data_response is None and remaining_attempts > 0:
            try:

                remaining_attempts -= 1
                if method == "get":
                    response = requests.get(
                        self.get_full_url(url), timeout=self._request_timeout, headers=headers, verify=self._https
                    )
                elif method == "post":
                    response = requests.post(
                        self.get_full_url(url),
                        timeout=self._request_timeout,
                        json=data,
                        headers=headers,
                        verify=self._https,
                    )
                else:
                    raise FreqSignalsError(f"bad method: {method}")

                if response.status_code < 200 or response.status_code >= 300:
                    self.log(
                        "error",
                        "make_load_request.error_status_code",
                        remaining_attempts=remaining_attempts,
                        data=data,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    if response.text:
                        raise FreqSignalsError(
                            "bad return status code: {} - {}".format(response.status_code, response.text)
                        )
                    else:
                        raise FreqSignalsError("bad return status code: {}".format(response.status_code))

                json_res = response.json()
                self.log(
                    "info",
                    "request.success",
                    remaining_attempts=remaining_attempts,
                    method=method,
                    url=url,
                    data=data,
                    status_code=response.status_code,
                    response=json_res,
                )
                return json_res

            except ConnectTimeout:
                self.log(
                    "error",
                    "request.timeout",
                    remaining_attempts=remaining_attempts,
                    method=method,
                    url=url,
                    data=data,
                )
                if remaining_attempts:
                    time.sleep(self._request_wait_interval)
                if not remaining_attempts:
                    raise FreqSignalsTimeoutError

            except RequestException:
                raise
        raise FreqSignalsTimeoutError()

    def get(self, url):
        return self.make_request(url=url, method="get", headers=self.get_headers())

    def post(self, url, data):
        return self.make_request(url=url, method="post", data=data, headers=self.get_headers())

    def post_signal(self, data):
        return self.post("/api/crud/signals/", data)

    def get_signals(self, filters=None):
        if filters is None:
            filters = {}
        query_params = urlencode({**filters})
        return self.get(f"/api/crud/signals/?{query_params}")

    def log(self, level, msg, **kwargs):
        """
        Logging function hook that should be overridden if you want logging
        Args:
            level: str - the level to log at
            msg: str - the message
            kwargs: dict - any logging vars

        Returns:
            None
        """
        pass



class FreqSignalsMixin:
    freqsignals_data_set_ids = None
    freqsignals_data_set_names = {}

    def freqsignals_init(self):
        """
        Called in __init__ to set up the required strategy instance variables
        """
        self.freqsignals_client = FreqSignalsClient()
        self.signals_by_pair_data_set_updated_date: Dict[str, Dict[str, Dict[str, Dict]]] = {}

    def freqsignals_bot_loop_start(self):
        """
        Called in bot_loop_start to pull the most recent signals and save in the strategy
        """
        if getattr(getattr(self, "config", {}).get('runmode'), "value", "none") in ('live', 'dry_run'):
            signal_filters = {}
            if self.freqsignals_data_set_ids:
                signal_filters["data_set_id__in"] = ','.join(self.freqsignals_data_set_ids)
            response = self.freqsignals_client.get_signals()
            signals = response["results"] 
            for signal in signals:
                if signal["symbol"] not in self.signals_by_pair_data_set_updated_date:
                    self.signals_by_pair_data_set_updated_date[signal["symbol"]] = {}
                if signal["data_set_id"] not in self.signals_by_pair_data_set_updated_date[signal["symbol"]]:
                    self.signals_by_pair_data_set_updated_date[signal["symbol"]][signal["data_set_id"]] = {}
                if signal["updated_date"] not in self.signals_by_pair_data_set_updated_date[signal["symbol"]][signal["data_set_id"]]:
                    self.signals_by_pair_data_set_updated_date[signal["symbol"]][signal["data_set_id"]][signal["updated_date"]] = signal
                    logger.info(f"received signal for {signal['symbol']} of {signal['value']}")

    def freqsignals_add_pair_signals(self, dataframe: DataFrame, pair: str, signal_name=None, data_set_id=None, include_context=False) -> DataFrame:
        """
        Called in populate_indicators to set the signals on the dataframe
        """

        signals_by_dataset = self.signals_by_pair_data_set_updated_date.get(pair, {})
        for data_set_id, signals in signals_by_dataset.items():
            for updated_date, signal in signals.items():
                if data_set_id:
                    if signal["data_set_id"] != data_set_id:
                        continue
                if signal_name is None:
                    signal_name = signal["data_set_id"]
                    if signal["data_set_id"] in self.freqsignals_data_set_names:
                        signal_name = self.freqsignals_data_set_names[signal["data_set_id"]]
                signal_start = datetime.fromisoformat(signal["updated_date"].replace("Z", ""))
                signal_end = signal_start + timedelta(minutes=signal["ttl_minutes"])
                dataframe.loc[(
                    (dataframe['date'] >= signal_start.isoformat()) &
                    (dataframe['date'] < signal_end.isoformat())
                ),
                signal_name] = signal["value"]

                if include_context and "context" in signal:
                    for k, v in signal["context"].items():
                        dataframe.loc[(
                            (dataframe['date'] >= signal_start.isoformat()) &
                            (dataframe['date'] < signal_end.isoformat())
                        ),
                        f"{signal_name}_{k}"] = v

        return dataframe


class FreqSignalsStrategy(IStrategy, FreqSignalsMixin):

    freqsignals_data_set_ids = ["e7041595-8851-4c80-aba5-944468ee7820"]
    freqsignals_data_set_names = {
        "e7041595-8851-4c80-aba5-944468ee7820": "signal"
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
                "signal": {}
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.freqsignals_init()

    def bot_loop_start(self, **kwargs) -> None:
        self.freqsignals_bot_loop_start()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.freqsignals_add_pair_signals(dataframe, "SPY", "signaled_move")
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(
            (dataframe['signal'] >= 0.01) &
            (dataframe['volume'] > 0)
        ),
        ['enter_long', 'enter_tag']] = (1, 'signal_bull')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(
            (dataframe['signal'] <= -0.01) &
            (dataframe['volume'] > 0)
        ),
        ['exit_long', 'exit_tag']] = (1, 'signal_bear')
        return dataframe
