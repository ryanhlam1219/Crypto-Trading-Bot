import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json
import threading
import csv

from datetime import datetime, timedelta
from math import floor
from Exchanges.exchange import Exchange

class BacktestClient(Exchange):
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        """
        Initializes the TestExchange instance.

        :param key: API key for authentication.
        :param secret: API secret for signing requests.
        :param currency: The base currency (e.g., 'BTC').
        :param asset: The quote asset (e.g., 'USDT').
        :param mode: The Trading mode ("Backtest" or "Trade") to see if responses should be mocked
        """
        self.apiKey = key
        self.apiSecret = secret
        self.name = None
        self.currency_asset = currency + asset

    def __get_binanceus_signature(self, data, secret):
        """
        Generates an HMAC SHA256 signature for Binance US API requests.

        :param data: The data to be signed.
        :param secret: The user's secret key.
        :return: The generated HMAC signature as a hexadecimal string.
        """
        postdata = urllib.parse.urlencode(data)
        message = postdata.encode()
        byte_key = bytes(secret, 'UTF-8')
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac

    def __submit_get_request(self, uri_path, data):
        """
        Sends a GET request to the Binance US API with authentication.

        :param uri_path: The API endpoint path.
        :param data: The payload to include in the request.
        :return: The response object from the request.
        """
        headers = {'X-MBX-APIKEY': self.apiKey}
        signature = self.get_binanceus_signature(data, self.apiSecret)
        payload = {**data, "signature": signature}
        response = requests.get(self.api_url + uri_path, params=payload, headers=headers)
        return response
    
    def __fetch_candle_data_from_time_interval(self, interval, start_time, end_time, results):
        """
        Fetch candlestick data for a specific time range and store in results list.

        :param interval: Time interval in minutes.
        :param start_time: Start time in milliseconds.
        :param end_time: End time in milliseconds.
        :param results: Shared list to store results.
        """
        uri_path = f'/api/v3/klines?symbol={self.currency_asset}&interval={interval}m'
        limit = 1000  # Max records per request
        local_data = []

        while start_time < end_time:
            response = requests.get(f'{self.api_url}{uri_path}&startTime={start_time}&limit={limit}')
            
            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}, {response.text}")
                break

            json_data = json.loads(response.text)
            if not json_data:
                break

            local_data.extend(json_data)
            start_time = json_data[-1][0] + 1  # Move past last returned candle

            # Adaptive sleep to handle rate limits
            time.sleep(0.2)  

        results.extend(local_data)

    def get_connectivity_status(self):
        """
        Checks the connectivity status to Binance US.

        :return: True if connected, False otherwise.
        """
        return True

    def get_account_status(self):
        """
        Retrieves the user's account status and prints it.
        """
        uri_path = '/sapi/v3/accountStatus'
        data = {"timestamp": int(round(time.time() * 1000))}
        response = self.__submit_get_request(uri_path, data)
        print("Account status:")
        print(json.dumps(json.loads(response.text), indent=2))

    def get_candle_stick_data(self, interval):
        """
        Fetches the latest candlestick (Kline) data for the given interval.

        :param interval: The interval in minutes (e.g., '1', '5', '15').
        :return: JSON response containing candlestick data.
        """
        uri_path = f'/api/v3/klines?symbol={self.currency_asset}&interval={interval}m'
        response = requests.get(self.api_url + uri_path)
        return json.loads(response.text)

    def write_candlestick_to_csv(self, data_list, filename="candlestick_data.csv"):
        """
        Writes multiple candlestick (Kline) data entries to a CSV file.

        :param data_list: List of lists, where each inner list contains candlestick data.
        :param filename: Name of the CSV file (default: 'candlestick_data.csv').
        """
        headers = [
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ]

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write column headers
            writer.writerows(data_list)  # Write multiple rows

        print(f"{len(data_list)} records successfully written to {filename}")

    def get_historical_candle_stick_data(self, interval, yearsPast, threads=5):
        """
        Fetches historical candlestick (Kline) data using parallel requests.

        :param interval: Time interval in minutes (e.g., '1m', '5m', '1h', '1d').
        :param yearsPast: Number of years in the past from which to start fetching data.
        :param threads: Number of parallel threads to use.
        :return: List of historical Kline data.
        """
        uri_path = '/api/v3/ping'
        response = requests.get(self.api_url + uri_path)
        if response.text != '{}':
            raise ConnectionError(f'Failed to connect to Binance Exchange for fetching historical data')
        current_time_ms = int(time.time() * 1000)
        start_time = current_time_ms - (yearsPast * 365 * 24 * 60 * 60 * 1000)
        end_time = current_time_ms

        total_range = end_time - start_time
        chunk_size = total_range // threads  # Divide time range into chunks

        all_candles = []
        threads_list = []
        results = []

        for i in range(threads):
            chunk_start = start_time + (i * chunk_size)
            chunk_end = start_time + ((i + 1) * chunk_size) if i < threads - 1 else end_time
            thread = threading.Thread(target=self.__fetch_candle_data_from_time_interval, args=(interval, chunk_start, chunk_end, results))
            threads_list.append(thread)
            thread.start()

        for thread in threads_list:
            thread.join()

        all_candles.extend(results)
        all_candles.sort(key=lambda x: x[0])  # Ensure data is sorted by timestamp

        return all_candles

    def submit_post_request(self, uri_path, data):
        """
        Sends a POST request to the Binance US API with authentication.

        :param uri_path: The API endpoint path.
        :param data: The payload to include in the request.
        :return: The response text from the request.
        """
        headers = {'X-MBX-APIKEY': self.apiKey}
        signature = self.__get_binanceus_signature(data, self.apiSecret)
        payload = {**data, "signature": signature}
        response = requests.post(self.api_url + uri_path, headers=headers, data=payload)
        return response.text

    def create_new_order(self, side, order_type, quantity):
        """
        Creates a new test order on Binance US.

        :param side: The order side ('BUY' or 'SELL').
        :param order_type: The order type ('MARKET', 'LIMIT', etc.).
        :param quantity: The quantity of the asset to order.
        """
        uri_path = "/api/v3/order/test"
        data = {
            "symbol": self.currency_asset,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": int(round(time.time() * 1000))
        }

        result = self.submit_post_request(uri_path, data)
        print(f"POST {uri_path}: {result}")