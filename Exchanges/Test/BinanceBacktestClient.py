import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json
import threading
import csv
from tqdm import tqdm

from math import floor
from ..exchange import Exchange
from Tests.utils import DataFetchException
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from threading import Lock

class BinanceBacktestClient(Exchange):
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str, metrics_collector):
        """
        Initializes BinanceBacktestClient using the Exchange superclass constructor.
        
        :param key: API key for authentication.
        :param secret: API secret for signing requests.
        :param currency: The base currency (e.g., USD).
        :param asset: The trading asset (e.g., BTC).
        :param metrics_collector: MetricsCollector instance for performance tracking.
        """
        super().__init__(key, secret, currency, asset, metrics_collector)  # Calls parent constructor
        self.test_data = []
        self.testIndex = 0
        self.strategy_pbar = None

    def initialize_strategy_progress_bar(self):
        """
        Initialize progress bar for strategy execution during backtest.
        """
        if len(self.test_data) > 0:
            self.strategy_pbar = tqdm(
                total=len(self.test_data),
                desc="Running backtest",
                unit="candles",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {rate_fmt}"
            )
        
    def close_strategy_progress_bar(self):
        """
        Close the strategy progress bar.
        """
        if self.strategy_pbar:
            self.strategy_pbar.close()
            self.strategy_pbar = None

    def __convert_minutes_to_binance_interval(self, minutes):
        """
        Convert minutes to proper Binance interval format.
        
        :param minutes: Number of minutes (int)
        :return: Binance interval string (e.g., '1m', '1h', '1d')
        """
        if minutes < 60:
            return f"{minutes}m"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            return f"{hours}h"
        else:  # Days
            days = minutes // 1440
            return f"{days}d"

    def __fetch_candle_data_from_time_interval(self, interval, start_time, end_time, results_lock: Lock, pbar=None):
        """
        Fetches candlestick data for a given time range and stores unique values in self.test_data.
        Uses a lock to prevent concurrent modification issues.
        """
        binance_interval = self.__convert_minutes_to_binance_interval(interval)
        uri_path = f'/api/v3/klines?symbol={self.currency_asset}&interval={binance_interval}'
        limit = 1000
        local_data = []  # List to store data before merging into test_data

        while start_time < end_time:
            response = requests.get(f'{self.api_url}{uri_path}&startTime={int(start_time)}&limit={limit}')
            
            if response.status_code != 200:
                if pbar:
                    pbar.write(f"Error fetching data: {response.status_code}, {response.text}")
                break

            json_data = response.json()  # Directly parse JSON response
            if not json_data:
                break

            # Ensure each element in json_data is a list before adding
            if all(isinstance(item, list) for item in json_data):
                local_data.extend(json_data)
            else:
                if pbar:
                    pbar.write("Warning: Received data is not a list of lists")

            start_time = json_data[-1][0] + 1  # Move to the next batch
            
            # Update progress bar if provided
            if pbar:
                pbar.update(len(json_data))
            
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

    def create_new_order(self, direction: TradeDirection, order_type: OrderType, quantity, price=None):
        """
        Mocks a new order for Backtesting

        :param direction: Trade direction (buy/sell).
        :param order_type: Type of order to place.
        :param quantity: Quantity of the asset to trade.
        :param price: Price for limit orders (optional, required for LIMIT orders).
        """
        start_time = time.time()

        data = {
            "symbol": self.currency_asset,
            "side": direction._value_,
            "type": self.__get_binance_order_type(order_type),
            "quantity": quantity,
            "timestamp": int(round(time.time() * 1000))
        }   

        # Simulate API response time for backtest
        response_time = time.time() - start_time
        
        # Record mock API call metrics
        self.metrics_collector.record_api_call(
            endpoint="/api/v3/order/test",
            method="POST",
            response_time=response_time,
            status_code=200,
            success=True
        )

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
        
        # Update progress bar if it exists
        if hasattr(self, 'strategy_pbar') and self.strategy_pbar:
            self.strategy_pbar.update(1)
            current_price = mockCandleStickData[4] if len(mockCandleStickData) > 4 else 0
            
            # Try to get P&L from metrics collector
            postfix_data = {"Price": f"${float(current_price):.2f}"}
            try:
                total_pnl = self.metrics_collector.calculate_total_profit_loss()
                postfix_data["PnL"] = f"${total_pnl:.2f}"
            except:
                pass  # If metrics calculation fails, just show price
            
            self.strategy_pbar.set_postfix(postfix_data)

        # **Ensure safety: Always return a list of lists**
        if not isinstance(mockCandleStickData, list):
            mockCandleStickData = [[mockCandleStickData]]
        elif not all(isinstance(item, list) for item in mockCandleStickData):
            mockCandleStickData = [mockCandleStickData] 

        return CandleStickData.from_list(mockCandleStickData[0])


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
        Fetches historical candlestick data using multithreading with progress bar.
        """
        # Verify API connectivity
        if requests.get(self.api_url + "/api/v3/ping").text != '{}':
            raise ConnectionError('Failed to connect to Binance Exchange')

        current_time_ms = int(time.time() * 1000)
        start_time = int(current_time_ms - (yearsPast * 365 * 24 * 60 * 60 * 1000))
        end_time = current_time_ms

        # Estimate total data points for progress bar
        total_range = end_time - start_time
        interval_ms = int(interval) * 60 * 1000  # Convert minutes to milliseconds
        estimated_candles = total_range // interval_ms

        # Define chunks for multithreading
        chunk_size = total_range // threads  

        results_lock = threading.Lock()  # Lock to prevent concurrent modification of self.test_data
        threads_list = []

        # Create progress bar for data fetching
        with tqdm(total=estimated_candles, 
                 desc=f"Fetching {self.currency_asset} data ({yearsPast}y)", 
                 unit="candles",
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {rate_fmt}") as pbar:
            
            for i in range(threads):
                chunk_start = start_time + (i * chunk_size)
                chunk_end = chunk_start + chunk_size if i < threads - 1 else end_time
                thread = threading.Thread(target=self.__fetch_candle_data_from_time_interval, 
                                        args=(interval, chunk_start, chunk_end, results_lock, pbar))
                threads_list.append(thread)
                thread.start()

            for thread in threads_list:
                thread.join()

        print(f"Successfully fetched {len(self.test_data)} candlestick data points")
        return self.test_data  # Return the updated test data
