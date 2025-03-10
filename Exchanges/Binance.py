import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json

from datetime import datetime
from math import floor
from Exchanges.exchange import Exchange
from Strategies.ExhcangeModels import CandleStickData, OrderType, TradeDirection

class Binance(Exchange):
    """
    A class representing an exchange for testing purposes, specifically interfacing with Binance US.
    """
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        """
        Initializes the TestExchange instance with API credentials and trading pair information.
        
        :param key: API key for authentication.
        :param secret: API secret for signing requests.
        :param currency: Base currency (e.g., USD).
        :param asset: Trading asset (e.g., BTC).
        """
        super().__init__(key, secret, currency, asset)

    def __get_binanceus_signature(self, data, secret):
        """
        Generates an HMAC SHA256 signature for Binance US API requests.
        
        :param data: Dictionary containing the request parameters.
        :param secret: API secret key used for signing.
        :return: Hexadecimal representation of the HMAC signature.
        """
        postdata = urllib.parse.urlencode(data)
        message = postdata.encode()
        byte_key = bytes(secret, 'UTF-8')
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac

    def __submit_get_request(self, uri_path, data):
        """
        Submits an authenticated GET request to the Binance US API.
        
        :param uri_path: API endpoint path.
        :param data: Dictionary containing request parameters.
        :return: Response object from the GET request.
        """
        headers = {'X-MBX-APIKEY': self.apiKey}
        signature = self.__get_binanceus_signature(data, self.apiSecret)
        payload = {**data, "signature": signature}
        response = requests.get((self.api_url + uri_path), params=payload, headers=headers)
        return response

    def get_connectivity_status(self):
        """
        Checks the connection status to Binance US.
        
        :return: True if the API is reachable, otherwise False.
        """
        uri_path = '/api/v3/ping'
        response = requests.get(self.api_url + uri_path)
        return True if response.text == '{}' else False
    
    def get_account_status(self):
        """
        Fetches and prints the user's Binance US account status.
        """
        uri_path = '/sapi/v3/accountStatus'
        data = {"timestamp": int(round(time.time() * 1000))}
        response = self.__submit_get_request(uri_path, data)
        print("Account status:")
        print(json.dumps(json.loads(response.text), indent=2))

    def get_candle_stick_data(self, interval):
        """
        Retrieves candlestick (K-line) data for the trading pair.
        
        :param interval: Time interval in minutes for the candlestick data.
        :return: JSON response containing candlestick data.
        """
        uri_path = f'/api/v3/klines?symbol={self.currency_asset}&interval={interval}m&limit=1'
        response = requests.get(self.api_url + uri_path)
        json_data = json.loads(response.text)
        return CandleStickData.from_list(json_data[0])

    def __submit_post_request(self, uri_path, data):
        """
        Submits an authenticated POST request to the Binance US API.
        
        :param uri_path: API endpoint path.
        :param data: Dictionary containing request parameters.
        :return: Response text from the POST request.
        """
        headers = {'X-MBX-APIKEY': self.apiKey}
        signature = self.__get_binanceus_signature(data, self.apiSecret)
        payload = {**data, "signature": signature}
        req = requests.post((self.api_url + uri_path), headers=headers, data=payload)
        return req.text

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
            "side": direction._value_,
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

        result = self.__submit_post_request(uri_path, data)
        print("POST {}: {}".format(uri_path, result))

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
