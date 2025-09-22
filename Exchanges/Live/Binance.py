import time
import json

from datetime import datetime
from math import floor
from ..exchange import Exchange
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from ApiProxy import APIProxy, ExchangeConfig

class Binance(Exchange):
    """
    A class representing an exchange for testing purposes, specifically interfacing with Binance US.
    """
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str, metrics_collector):
        """
        Initializes the Binance instance with API credentials and trading pair information.
        
        :param key: API key for authentication.
        :param secret: API secret for signing requests.
        :param currency: The base currency (e.g., USD).
        :param asset: The trading asset (e.g., BTC).
        :param metrics_collector: MetricsCollector instance for performance tracking.
        """
        super().__init__(key, secret, currency, asset, metrics_collector)
        
        # Initialize API Proxy
        config = ExchangeConfig.create_binance_config(key, secret)
        self.api_proxy = APIProxy(config)

    def get_connectivity_status(self):
        """
        Checks the connection status to Binance US.
        
        :return: True if the API is reachable, otherwise False.
        """
        try:
            response = self.api_proxy.make_public_request('GET', '/api/v3/ping')
            return response == {}
        except Exception:
            return False
    
    def get_account_status(self):
        """
        Retrieves the account status for the authenticated user.
        """
        try:
            response = self.api_proxy.make_request('GET', '/sapi/v3/accountStatus')
            if self.metrics_collector:
                self.metrics_collector.record_api_call(endpoint='/sapi/v3/accountStatus', method='GET', success=True)
            print("Account status:")
            print(json.dumps(response, indent=2))
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_api_call(endpoint='/sapi/v3/accountStatus', method='GET', success=False, error_message=str(e))
            raise

    def get_candle_stick_data(self, interval):
        """
        Retrieves candlestick (K-line) data for the trading pair.
        
        :param interval: Time interval in minutes for the candlestick data.
        :return: JSON response containing candlestick data.
        """
        params = {
            'symbol': self.currency_asset,
            'interval': f'{interval}m',
            'limit': 1
        }
        response = self.api_proxy.make_public_request('GET', '/api/v3/klines', params)
        return CandleStickData.from_list(response[0])

    def create_new_order(self, direction: TradeDirection, order_type: OrderType, quantity, price=None, time_in_force="GTC"):
        """
        Creates a new order on Binance US.

        :param direction: Trade direction (buy/sell).
        :param order_type: Type of order to place.
        :param quantity: Quantity of the asset to trade.
        :param price: Price for limit orders (optional, required for LIMIT orders).
        :param time_in_force: Time-in-force policy (default: "GTC").
        """
        start_time = time.time()
        endpoint = "/api/v3/order/test"

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

        params = {
            "symbol": self.currency_asset,
            "side": direction._value_,
            "type": self.__get_binance_order_type(order_type),
            "quantity": validated_quantity
        }

        # Ensure price is included for LIMIT orders
        if order_type == OrderType.LIMIT_ORDER:
            if validated_price is None:
                raise ValueError("Price must be provided for LIMIT orders.")
            params["price"] = validated_price
            params["timeInForce"] = time_in_force  # Required for limit orders

        try:
            result = self.api_proxy.make_request('POST', endpoint, params)
            response_time = time.time() - start_time
            
            # Record API call metrics
            self.metrics_collector.record_api_call(
                endpoint=endpoint,
                method="POST",
                response_time=response_time,
                status_code=200,  # Assuming success if no exception
                success=True
            )
            
            print("POST {}: {}".format(endpoint, result))
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Record API error metrics
            self.metrics_collector.record_api_call(
                endpoint=endpoint,
                method="POST",
                response_time=response_time,
                status_code=500,  # Assuming server error
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
            return str(order_mapping[order_type])
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

    def __del__(self):
        """Clean up API proxy when object is destroyed"""
        if hasattr(self, 'api_proxy'):
            self.api_proxy.close()
