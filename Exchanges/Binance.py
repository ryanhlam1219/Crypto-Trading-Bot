import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json

from datetime import datetime
from math import floor

class Binance():
    api_url = "https://api.binance.us"

    def __init__(self, key: str, secret: str):
        self.key = key
        self.secret = secret
        self.name = self.__class__.__name__

     # get binanceus signature
    def get_binanceus_signature(self, data, secret):
        postdata = urllib.parse.urlencode(data)
        message = postdata.encode()
        byte_key = bytes(secret, 'UTF-8')
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac

    def submitGetRequest(self, uri_path):
        data = {
            "timestamp": int(round(time.time() * 1000)),
        }
        headers = {}
        headers['X-MBX-APIKEY'] = self.key
        signature = self.get_binanceus_signature(data, self.secret)
        params={
            **data,
            "signature": signature,
        }
        response = requests.get((self.api_url + uri_path), params=params, headers=headers)
        return response

    def getAccountStatus(self):
        uri_path = '/sapi/v3/accountStatus'
        response = self.submitGetRequest(uri_path)
        print("Account status:")
        print(json.dumps(json.loads(response.text)))

    #takes in a list of symbols and returns 500 (default) candlesticks in 1 minute intervals
    #using the most recent klines in USD
    def getCandleStickData(self, symbol):
        uri_path = '/api/v3/klines?symbol=' + symbol + '&interval=1m'
        response = requests.get(self.api_url + uri_path)
        print(json.dumps(json.loads(response.text)))

