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

class Binance(Exchange):
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        self.apiKey = key
        self.apiSecret = secret
        self.name = None
        self.currency_asset = currency + asset

    # Generates an endpoint signature for get requests associated with the user's account
    # @Param data: the data required to send to the endpoint
    # @Param secret: the user's secret key
    def get_binanceus_signature(self, data, secret):
        postdata = urllib.parse.urlencode(data)
        message = postdata.encode()
        byte_key = bytes(secret, 'UTF-8')
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac

    # Submits a get request for a user with a given endpoint signature
    # @Param uri_path: the API endpoint path to use in order to submit the request
    def submitGetRequestForEndpoint(self, uri_path):
        data = {
            "timestamp": int(round(time.time() * 1000)),
        }
        headers = {}
        headers['X-MBX-APIKEY'] = self.apiKey
        signature = self.get_binanceus_signature(data, self.apiSecret)
        params={
            **data,
            "signature": signature,
        }
        response = requests.get((self.api_url + uri_path), params=params, headers=headers)
        return response

    # @Override
    # returns the connection status to Binance US
    def getConnectivityStatus(self):
        uri_path = '/api/v3/ping'
        response = requests.get(self.api_url + uri_path)
        return True if response.text == '{}' else False
    
    # returns the user's account status
    def getAccountStatus(self):
        uri_path = '/sapi/v3/accountStatus'
        response = self.submitGetRequestForEndpoint(uri_path)
        print("Account status:")
        print(json.dumps(json.loads(response.text), indent=2))

    # @Override
    # Pulls the current candlestick data for a given symbol
    # @Param interval: the interval in minutes for which to fetch candlestick data 
    def getCandleStickData(self, interval):
        uri_path = '/api/v3/klines?symbol=' + self.currency_asset + f'&interval={interval}m'
        response = requests.get(self.api_url + uri_path)
        json_data = json.loads(response.text)
        return json_data



