import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json
import threading
import csv

from math import floor
from Exchanges.exchange import Exchange
from Test.DataFetchException import DataFetchException
from Strategies.ExhcangeModels import CandleStickData, OrderType, TradeDirection
from threading import Lock

class KrakenBackTestClient(Exchange):
    api_url = "https://api.kraken.com"

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        super().__init__(key, secret, currency, asset) #calls parent constructor
        self.test_data = []
        self.testIndex = 0
    # ---------- Helpers ----------
    def __to_kraken_pair(self) -> str:
        """
        Convert self.currency_asset (e.g., 'BTCUSD') to a Kraken pair (e.g., 'XBTUSD').
        Kraken accepts 'XBTUSD', 'ETHUSD', etc. (no need for the legacy XXBTZUSD form).
        """
        # Basic mapper for common assets
        asset_map = {
            "BTC": "XBT",
            "XBT": "XBT",
            "ETH": "ETH",
            "SOL": "SOL",
            "ADA": "ADA",
            "LTC": "LTC",
            "XRP": "XRP",
            "DOGE": "DOGE",
            "DOT": "DOT",
            "USDT": "USDT",
            "USDC": "USDC",
            "EUR": "EUR",
            "USD": "USD",
        }
        # Split self.currency_asset like 'BTCUSD' into ('BTC','USD')
        base = self.asset.upper()     # e.g., BTC
        quote = self.currency.upper() # e.g., USD

        base = asset_map.get(base, base)
        quote = asset_map.get(quote, quote)

        return f"{base}{quote}"  # e.g., XBTUSD

    @staticmethod
    def __get_kraken_order_type(order_type: OrderType):
        """
        Maps your generic order types to Kraken names (kept only for parity; orders are mocked).
        """
        mapping = {
            OrderType.LIMIT_ORDER: "limit",
            OrderType.MARKET_ORDER: "market",
            OrderType.STOP_LIMIT_ORDER: "stop-loss-limit",   # closest analogue
            OrderType.TAKE_PROFIT_LIMIT_ORDER: "take-profit-limit",
            OrderType.LIMIT_MAKER_ORDER: "post-only"         # via flag on Kraken, modeled here nominally
        }
        if order_type in mapping:
            return mapping[order_type]
        raise ValueError(f"Unsupported order type: {order_type}")

    def get_connectivity_status(self):
        """
        Checks connectivity to Kraken public API (lightweight).
        """
        try:
            r = requests.get(self.api_url + "/0/public/Time", timeout=5)
            return r.status_code == 200 and "result" in r.json()
        except Exception:
            return False

    def get_account_status(self):
        """
        Backtest client: no real account calls.
        """
        print("Account status: Mocked due to Kraken Pro BacktestClient usage")
    
    def create_new_order(self, direction: TradeDirection, order_type: OrderType, quantity, price=None):
        """
        Mock order (for parity with BinanceBacktestClient).
        """
        data = {
            "pair": self.__to_kraken_pair(),
            "side": direction._value_,
            "type": self.__get_kraken_order_type(order_type),
            "quantity": quantity,
            "price": price,
            "timestamp": int(round(time.time() * 1000))
        }
        print(f"Executing Mock order {data}")
        
    # ---------- Data fetching & normalization ----------

    def __fetch_candle_data_from_time_interval(self, interval_min: int, start_ms: int, end_ms: int, results_lock: Lock):
        """
        Fetches OHLC data from Kraken for [start_ms, end_ms) and appends to self.test_data.
        Normalizes each candle to a Binance-style 12-field kline for compatibility.
        """
        pair = self.__to_kraken_pair()
        local_data = []

        # Kraken uses seconds for 'since'
        since_sec = max(0, start_ms // 1000)
        end_sec = end_ms // 1000
        interval = int(interval_min)  # minutes
        per_candle_secs = interval * 60

        while since_sec < end_sec:
            url = f"{self.api_url}/0/public/OHLC"
            params = {"pair": pair, "interval": interval, "since": since_sec}
            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                print(f"Error fetching data: {resp.status_code}, {resp.text}")
                break
            payload = resp.json()
            if "error" in payload and payload["error"]:
                print(f"Kraken error: {payload['error']}")
                break

            result = payload.get("result", {})
            # Kraken returns a dict with key == canonical pair name
            # We don't know the exact canonical key, so pick the first list in result (excluding 'last')
            ohlc_key = None
            for k, v in result.items():
                if k != "last" and isinstance(v, list):
                    ohlc_key = k
                    break

            if ohlc_key is None:
                # Nothing useful returned
                break

            candles = result.get(ohlc_key, [])
            if not candles:
                break

            # Each candle: [time, open, high, low, close, vwap, volume, count]
            # Normalize to Binance-like 12-tuple:
            # [openTime, open, high, low, close, volume,
            #  closeTime, quoteAssetVolume, numberOfTrades,
            #  takerBuyBaseAssetVolume, takerBuyQuoteAssetVolume, ignore]
            for c in candles:
                try:
                    t_sec, o, h, l, cl, vwap, vol, count = c
                    open_time_ms = int(t_sec) * 1000
                    close_time_ms = open_time_ms + per_candle_secs * 1000 - 1

                    # Derive quote volume ~ base_volume * vwap when available
                    quote_vol = float(vol) * float(vwap) if vwap not in (None, 0, "0") else 0.0

                    normalized = [
                        open_time_ms,               # Open Time
                        str(o),                     # Open
                        str(h),                     # High
                        str(l),                     # Low
                        str(cl),                    # Close
                        str(vol),                   # Volume (base)
                        close_time_ms,              # Close Time
                        str(quote_vol),             # Quote Asset Volume (approx)
                        int(count),                 # Number of Trades
                        "0",                        # Taker Buy Base Asset Volume (unknown) -> "0"
                        "0",                        # Taker Buy Quote Asset Volume (unknown) -> "0"
                        "0"                         # Ignore
                    ]

                    # Only append if within requested range
                    if open_time_ms >= start_ms and open_time_ms < end_ms:
                        local_data.append(normalized)
                except Exception as e:
                    print(f"Skipping malformed candle {c}: {e}")

            # Advance 'since' to the last candle open time + interval
            # Kraken also returns 'last' (the id to use as next since), but stepping by interval is fine.
            last_open_sec = candles[-1][0] if candles else since_sec
            since_sec = max(since_sec + per_candle_secs, int(last_open_sec) + per_candle_secs)

            # Gentle sleep to be nice to the public API
            time.sleep(0.1)

        # Thread-safe merge
        with results_lock:
            self.test_data.extend(local_data)

    def get_candle_stick_data(self, interval):
        """
        Return the next normalized kline as CandleStickData (matches your Binance flow).
        """
        if self.testIndex >= len(self.test_data):
            raise DataFetchException("No more candlestick data available", error_code=404)

        row = self.test_data[self.testIndex]
        self.testIndex += 1
        pct = 100.0 * (self.testIndex / len(self.test_data))
        print(f"Completion Percentage: {pct}%")

        # Ensure list-of-lists for from_list compatibility
        if not isinstance(row, list):
            row = [row]
        elif not all(isinstance(item, (int, float, str)) for item in row):
            row = [row]

        return CandleStickData.from_list(row)  # already a single 12-field list

    def write_candlestick_to_csv(self, data, filename="candlestick_data.csv"):
        """
        Writes normalized klines (Binance-style fields) to CSV.
        """
        headers = [
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ]

        data_list = data
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data_list)

        print(f"{len(data_list)} records successfully written to {filename}")

    def get_historical_candle_stick_data(self, interval, yearsPast, threads=5):
        """
        Multithreaded historical fetch using Kraken OHLC, normalized to Binance-style klines.
        """
        # Quick connectivity check
        try:
            pong = requests.get(self.api_url + "/0/public/SystemStatus", timeout=5)
            if pong.status_code != 200:
                raise ConnectionError("Failed to connect to Kraken Exchange")
        except Exception:
            raise ConnectionError("Failed to connect to Kraken Exchange")

        current_time_ms = int(time.time() * 1000)
        start_time = current_time_ms - int(yearsPast * 365 * 24 * 60 * 60 * 1000)
        end_time = current_time_ms

        total_range = end_time - start_time
        chunk_size = total_range // max(1, int(threads))

        results_lock = threading.Lock()
        threads_list = []

        for i in range(threads):
            chunk_start = start_time + (i * chunk_size)
            chunk_end = chunk_start + chunk_size if i < threads - 1 else end_time
            t = threading.Thread(
                target=self.__fetch_candle_data_from_time_interval,
                args=(interval, chunk_start, chunk_end, results_lock)
            )
            threads_list.append(t)
            t.start()

        for t in threads_list:
            t.join()

        # Optional: sort by open time to ensure sequence
        self.test_data.sort(key=lambda r: r[0])

        return self.test_data
