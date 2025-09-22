import time
import json
from typing import TYPE_CHECKING

from math import floor
from ..exchange import Exchange
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from ApiProxy import APIProxy, ExchangeConfig

if TYPE_CHECKING:
    from Utils.MetricsCollector import MetricsCollector


class TestExchange(Exchange):
    """
    A class representing an exchange for testing purposes, specifically interfacing with Binance US.
    """
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str, metrics_collector: "MetricsCollector"):
        """
        Initializes a test exchange client with mock data.
        
        :param key: API key (not used in test mode).
        :param secret: API secret (not used in test mode).
        :param currency: Base currency for trading (e.g., USD).
        :param asset: Trading asset (e.g., BTC).
        :param metrics_collector: MetricsCollector instance for performance tracking.
        """
        super().__init__(key, secret, currency, asset, metrics_collector)
        
        # Initialize API Proxy with Binance US configuration
        self.api_proxy = APIProxy(ExchangeConfig.create_binance_config(key, secret))
        
        # Default test data for predictable testing
        self.test_data = [
            [
                1640995200000,    # Open time
                "47000.0",        # Open price
                "47500.0",        # High price
                "46500.0",        # Low price
                "47200.0",        # Close price
                "100.0",          # Volume
                1640995260000,    # Close time
                "4720000.0",      # Quote asset volume
                50,               # Number of trades
                "50.0",           # Taker buy base asset volume
                "2360000.0",      # Taker buy quote asset volume
                "0"               # Ignore
            ]
        ]

    def __submit_get_request(self, uri_path, data):
        """
        Submits an authenticated GET request to the Binance US API.
        
        :param uri_path: API endpoint path.
        :param data: Dictionary containing request parameters.
        :return: Response object from the GET request.
        """
        return self.api_proxy.make_request('GET', uri_path, params=data)

    def get_connectivity_status(self):
        """
        Checks the connection status to Binance US.
        
        :return: True if the API is reachable, otherwise False.
        """
        uri_path = '/api/v3/ping'
        response = self.api_proxy.make_public_request('GET', uri_path)
        return response == {}
    
    def get_account_status(self):
        """
        Fetches and prints the user's Binance US account status.
        Since this is a test exchange, return mocked status instead of real API call.
        """
        print("Account status: Mocked due to TestExchange usage")

    def get_candle_stick_data(self, interval):
        """
        Retrieves candlestick (K-line) data for the trading pair.
        Returns test data instead of making real API calls.
        
        :param interval: Time interval in minutes for the candlestick data.
        :return: CandleStickData object containing test candlestick data.
        """
        if not self.test_data:
            raise IndexError("No test data available")
        
        return CandleStickData.from_list(self.test_data[0])

    def __submit_post_request(self, uri_path, data):
        """
        Submits an authenticated POST request to the Binance US API.
        
        :param uri_path: API endpoint path.
        :param data: Dictionary containing request parameters.
        :return: Response text from the POST request.
        """
        response = self.api_proxy.make_request('POST', uri_path, params=data)
        return response.get('msg', 'Success') if response else 'Error'

    def create_new_order(self, direction: TradeDirection, order_type: OrderType, quantity, price=None, time_in_force="GTC"):
        """
        Creates a new order on Binance US.

        :param direction: Trade direction (buy/sell).
        :param order_type: Type of order to place.
        :param quantity: Quantity of the asset to trade.
        :param price: Price for limit orders (optional, required for LIMIT orders).
        :param time_in_force: Time-in-force policy (default: "GTC").
        """
        uri_path = "/api/v3/order/test"

        data = {
            "symbol": self.currency_asset,
            "side": direction.value,
            "type": self.__get_binance_order_type(order_type),
            "quantity": quantity,
            "timestamp": int(round(time.time() * 1000))
        }

        # Ensure price is included for LIMIT orders
        if order_type == OrderType.LIMIT_ORDER:
            if price is None:
                raise ValueError("Price must be provided for LIMIT orders.")
            data["price"] = price
            data["timeInForce"] = time_in_force  # Required for limit orders

        try:
            start_time = time.time()
            result = self.__submit_post_request(uri_path, data)
            response_time = time.time() - start_time
            
            # Record API call metrics
            self.metrics_collector.record_api_call(
                endpoint=uri_path,
                method="POST",
                response_time=response_time,
                status_code=200,
                success=True
            )
            
            print("POST {}: {}".format(uri_path, result))
            
        except Exception as e:
            # Record API error metrics
            self.metrics_collector.record_api_call(
                endpoint=uri_path,
                method="POST", 
                response_time=time.time() - start_time if 'start_time' in locals() else 0,
                status_code=500,
                success=False,
                error_message=str(e)
            )
            raise


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
            return order_mapping[order_type]
        else:
            raise ValueError(f"Unsupported order type: {order_type}")
