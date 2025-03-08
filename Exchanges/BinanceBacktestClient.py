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
from Test.DataFetchException import DataFetchException
from Strategies.OrderTypes import OrderType
from Strategies.OrderTypes import TradeDirection
from threading import Lock

class BinanceBacktestClient(Exchange):
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        """
        Initializes BinanceBacktestClient using the Exchange superclass constructor.
        """
        super().__init__(key, secret, currency, asset)  # Calls parent constructor
        self.test_data = []
        self.testIndex = 0

    def __fetch_candle_data_from_time_interval(self, interval, start_time, end_time, results_lock: Lock):
        """
        Fetches candlestick data for a given time range and stores unique values in self.test_data.
        Uses a lock to prevent concurrent modification issues.
        """
        uri_path = f'/api/v3/klines?symbol={self.currency_asset}&interval={interval}m'
        limit = 1000
        local_data = []  # List to store data before merging into test_data

        while start_time < end_time:
            response = requests.get(f'{self.api_url}{uri_path}&startTime={start_time}&limit={limit}')
            
            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}, {response.text}")
                break

            json_data = response.json()  # Directly parse JSON response
            if not json_data:
                break

            # Ensure each element in json_data is a list before adding
            if all(isinstance(item, list) for item in json_data):
                local_data.extend(json_data)
            else:
                print("Warning: Received data is not a list of lists")

            start_time = json_data[-1][0] + 1  # Move to the next batch
            time.sleep(0.2)

        # Merge local data into self.test_data in a thread-safe way
        with results_lock:
            self.test_data.extend(local_data)  # Ensures test_data remains a list of lists

    @staticmethod
    def __get_binance_order_type(order_type: OrderType):
        """
        Converts a custom order type to a Binance-compatible order type.
        
        :param order_type: Custom order type.
        :return: Binance-compatible order type.
        :raises ValueError: If the order type is not supported.
        """
        order_mapping = {
            OrderType.LIMIT_ORDER: "LIMIT",
            OrderType.MARKET_ORDER: "MARKET",
            OrderType.STOP_LIMIT_ORDER: "STOP_LOSS_LIMIT",
            OrderType.TAKE_PROFIT_LIMIT_ORDER: "TAKE_PROFIT_LIMIT",
            OrderType.LIMIT_MAKER_ORDER: "LIMIT_MAKER"
        }

        if order_type in order_mapping:
            return str(order_mapping[order_type])
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

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
        print("Account status: Mocked due to Binance BacktestClient usage")

    def create_new_order(self, direction: TradeDirection, order_type: OrderType, quantity):
        """
        Mocks a new order for Backtesting

        :param direction: Trade direction (buy/sell).
        :param order_type: Type of order to place.
        :param quantity: Quantity of the asset to trade.
        :param price: Price for limit orders (optional, required for LIMIT orders).
        :param time_in_force: Time-in-force policy (default: "GTC").
        """

        data = {
            "symbol": self.currency_asset,
            "side": direction,
            "type": self.__get_binance_order_type(order_type),
            "quantity": quantity,
            "timestamp": int(round(time.time() * 1000))
        }   

        print(f"Executing Mock order {data}")


    def get_candle_stick_data(self, interval):
        """
        Fetches the latest candlestick (Kline) data for the given interval.
        Ensures that the returned value is always a list of lists.
        """
        if self.testIndex >= len(self.test_data):
            raise DataFetchException("No more candlestick data available", error_code=404)

        mockCandleStickData = self.test_data[self.testIndex]
        self.testIndex += 1
        dataAccessPercentage = 100.00 * (self.testIndex / len(self.test_data))
        print(f"Completion Percentage: {dataAccessPercentage}%")

        # **Ensure safety: Always return a list of lists**
        if not isinstance(mockCandleStickData, list):
            mockCandleStickData = [[mockCandleStickData]]
        elif not all(isinstance(item, list) for item in mockCandleStickData):
            mockCandleStickData = [mockCandleStickData] 

        return mockCandleStickData


    def write_candlestick_to_csv(self, data, filename="candlestick_data.csv"):
        """
        Writes multiple candlestick (Kline) data entries to a CSV file.

        :param data: A dictionary (timestamp -> candlestick data) or a list of lists.
        :param filename: Name of the CSV file (default: 'candlestick_data.csv').
        """
        headers = [
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ]

        data_list = data  # Assume it's already a list of lists

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write column headers
            writer.writerows(data_list)  # Write multiple rows

        print(f"{len(data_list)} records successfully written to {filename}")

    def get_historical_candle_stick_data(self, interval, yearsPast, threads=5):
        """
        Fetches historical candlestick data using multithreading.
        """
        # Verify API connectivity
        if requests.get(self.api_url + "/api/v3/ping").text != '{}':
            raise ConnectionError('Failed to connect to Binance Exchange')

        current_time_ms = int(time.time() * 1000)
        start_time = current_time_ms - (yearsPast * 365 * 24 * 60 * 60 * 1000)
        end_time = current_time_ms

        # Define chunks for multithreading
        total_range = end_time - start_time
        chunk_size = total_range // threads  

        results_lock = threading.Lock()  # Lock to prevent concurrent modification of self.test_data
        threads_list = []

        for i in range(threads):
            chunk_start = start_time + (i * chunk_size)
            chunk_end = chunk_start + chunk_size if i < threads - 1 else end_time
            thread = threading.Thread(target=self.__fetch_candle_data_from_time_interval, args=(interval, chunk_start, chunk_end, results_lock))
            threads_list.append(thread)
            thread.start()

        for thread in threads_list:
            thread.join()

        return self.test_data  # Return the updated test data
