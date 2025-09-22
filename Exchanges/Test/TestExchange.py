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
        Fetches real data from Binance API.
        
        :param interval: Time interval in minutes for the candlestick data.
        :return: CandleStickData object containing real candlestick data.
        """
        params = {
            'symbol': self.currency_asset,
            'interval': f'{interval}m',
            'limit': 1
        }
        response = self.api_proxy.make_public_request('GET', '/api/v3/klines', params)
        return CandleStickData.from_list(response[0])

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
        Creates a new order on Binance US with proper validation and adjustments.

        :param direction: Trade direction (buy/sell).
        :param order_type: Type of order to place.
        :param quantity: Quantity of the asset to trade.
        :param price: Price for limit orders (optional, required for LIMIT orders).
        :param time_in_force: Time-in-force policy (default: "GTC").
        """
        uri_path = "/api/v3/order/test"

        # Validate and adjust order parameters
        if order_type == OrderType.LIMIT_ORDER and price is not None:
            validated_price = self._validate_and_adjust_price(price)
            validated_quantity = self._validate_and_adjust_quantity(quantity, validated_price)
            print(f"📊 Order Validation: Original qty={quantity}, price=${price:.6f}")
            print(f"📊 Order Validation: Adjusted qty={validated_quantity}, price=${validated_price:.6f}")
            print(f"📊 Order Validation: Notional value=${validated_quantity * validated_price:.2f}")
        else:
            validated_price = price
            validated_quantity = quantity

        data = {
            "symbol": self.currency_asset,
            "side": direction.value,
            "type": self.__get_binance_order_type(order_type),
            "quantity": validated_quantity,
            "timestamp": int(round(time.time() * 1000))
        }

        # Ensure price is included for LIMIT orders
        if order_type == OrderType.LIMIT_ORDER:
            if validated_price is None:
                raise ValueError("Price must be provided for LIMIT orders.")
            data["price"] = validated_price
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

    def _validate_and_adjust_price(self, price: float) -> float:
        """Validate and adjust price to meet exchange requirements."""
        if "DOGE" in self.currency_asset:
            tick_size = 0.00001
            adjusted_price = round(price / tick_size) * tick_size
            return round(adjusted_price, 5)
        elif "BTC" in self.currency_asset:
            tick_size = 0.01
            adjusted_price = round(price / tick_size) * tick_size
            return round(adjusted_price, 2)
        else:
            tick_size = 0.0001
            adjusted_price = round(price / tick_size) * tick_size
            return round(adjusted_price, 4)

    def _validate_and_adjust_quantity(self, quantity: float, price: float) -> float:
        """Validate and adjust quantity to meet minimum notional requirements."""
        notional_value = quantity * price
        
        if "DOGE" in self.currency_asset:
            min_notional = 10.0  # $10 minimum for DOGE
            if notional_value < min_notional:
                required_quantity = max(1, int(min_notional / price) + 1)
                print(f"⚠️  MIN_NOTIONAL Adjustment: ${notional_value:.2f} < ${min_notional:.2f}")
                print(f"   Increasing quantity from {quantity} to {required_quantity}")
                return required_quantity
        elif "BTC" in self.currency_asset:
            min_notional = 10.0  # $10 minimum for BTC
            if notional_value < min_notional:
                required_quantity = max(0.0001, min_notional / price)  # BTC has smaller lot sizes
                print(f"⚠️  MIN_NOTIONAL Adjustment: ${notional_value:.2f} < ${min_notional:.2f}")
                print(f"   Increasing quantity from {quantity} to {required_quantity:.4f}")
                return round(required_quantity, 4)
        
        return quantity


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
