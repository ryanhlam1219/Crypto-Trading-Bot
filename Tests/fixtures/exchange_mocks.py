"""
Mock data and fixtures for exchange testing.
"""

from typing import Dict, Any, List


class MockExchangeResponses:
    """Standard mock responses for different exchanges."""
    
    @staticmethod
    def binance_connectivity_success():
        """Mock successful Binance connectivity check."""
        return {"status": 0}
    
    @staticmethod
    def binance_account_status():
        """Mock Binance account status response."""
        return {
            "status": "ACTIVE",
            "balances": [
                {
                    "asset": "USD",
                    "free": "10000.00000000",
                    "locked": "0.00000000"
                },
                {
                    "asset": "BTC", 
                    "free": "1.00000000",
                    "locked": "0.00000000"
                }
            ]
        }
    
    @staticmethod
    def binance_candlestick_data():
        """Mock Binance candlestick response."""
        return [
            [
                1634567890000,      # Open time
                "50000.00000000",   # Open price
                "51000.00000000",   # High price
                "49500.00000000",   # Low price
                "50500.00000000",   # Close price
                "1000.00000000",    # Volume
                1634567950000,      # Close time
                "50500000.00000000", # Quote asset volume
                100,                # Number of trades
                "600.00000000",     # Taker buy base asset volume
                "30300000.00000000" # Taker buy quote asset volume
            ]
        ]
    
    @staticmethod
    def binance_order_success():
        """Mock successful order creation response."""
        return {
            "orderId": 123456789,
            "symbol": "BTCUSD",
            "status": "FILLED",
            "clientOrderId": "test_order_1",
            "price": "50000.00000000",
            "origQty": "1.00000000",
            "executedQty": "1.00000000",
            "type": "LIMIT",
            "side": "BUY",
            "timeInForce": "GTC"
        }
    
    @staticmethod
    def binance_order_error():
        """Mock failed order creation response."""
        return {
            "code": -1013,
            "msg": "Invalid quantity."
        }
    
    @staticmethod
    def api_error_responses():
        """Various API error responses for testing."""
        return {
            "rate_limit": {"code": -1003, "msg": "Too many requests."},
            "invalid_api_key": {"code": -2014, "msg": "API-key format invalid."},
            "insufficient_balance": {"code": -2010, "msg": "Account has insufficient balance."},
            "invalid_symbol": {"code": -1121, "msg": "Invalid symbol."}
        }


class MockAPIEndpoints:
    """Mock HTTP endpoints and their expected responses."""
    
    BINANCE_ENDPOINTS = {
        "/api/v3/ping": MockExchangeResponses.binance_connectivity_success(),
        "/sapi/v3/accountStatus": MockExchangeResponses.binance_account_status(),
        "/api/v3/klines": MockExchangeResponses.binance_candlestick_data(),
        "/api/v3/order": MockExchangeResponses.binance_order_success()
    }


class CandlestickDataBuilder:
    """Builder for creating test candlestick data."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset to default values."""
        self.data = {
            'open_time': 1634567890000,
            'open_price': 50000.0,
            'high_price': 51000.0,
            'low_price': 49500.0,
            'close_price': 50500.0,
            'volume': 1000.0,
            'close_time': 1634567950000,
            'quote_asset_volume': 50500000.0,
            'num_trades': 100,
            'taker_buy_base_asset_volume': 600.0,
            'taker_buy_quote_asset_volume': 30300000.0
        }
        return self
    
    def with_price_range(self, open_price: float, close_price: float):
        """Set specific open and close prices."""
        self.data['open_price'] = open_price
        self.data['close_price'] = close_price
        # Adjust high/low to be realistic
        self.data['high_price'] = max(open_price, close_price) * 1.02
        self.data['low_price'] = min(open_price, close_price) * 0.98
        return self
    
    def with_high_volatility(self):
        """Create high volatility scenario."""
        base_price = self.data['open_price']
        self.data['high_price'] = base_price * 1.05
        self.data['low_price'] = base_price * 0.95
        return self
    
    def with_low_volatility(self):
        """Create low volatility scenario."""
        base_price = self.data['open_price']
        self.data['high_price'] = base_price * 1.001
        self.data['low_price'] = base_price * 0.999
        return self
    
    def with_timestamp(self, timestamp: int):
        """Set specific timestamp."""
        self.data['open_time'] = timestamp
        self.data['close_time'] = timestamp + 60000  # 1 minute later
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the candlestick data."""
        return self.data.copy()
    
    def build_list(self) -> List:
        """Build as list format (like API response)."""
        return [
            self.data['open_time'],
            str(self.data['open_price']),
            str(self.data['high_price']),
            str(self.data['low_price']),
            str(self.data['close_price']),
            str(self.data['volume']),
            self.data['close_time'],
            str(self.data['quote_asset_volume']),
            self.data['num_trades'],
            str(self.data['taker_buy_base_asset_volume']),
            str(self.data['taker_buy_quote_asset_volume'])
        ]


# Predefined test scenarios
PRICE_SCENARIOS = {
    'bull_market': [
        CandlestickDataBuilder().with_price_range(50000, 50500).build(),
        CandlestickDataBuilder().with_price_range(50500, 51000).build(),
        CandlestickDataBuilder().with_price_range(51000, 51800).build(),
    ],
    'bear_market': [
        CandlestickDataBuilder().with_price_range(50000, 49500).build(),
        CandlestickDataBuilder().with_price_range(49500, 49000).build(),
        CandlestickDataBuilder().with_price_range(49000, 48200).build(),
    ],
    'sideways_market': [
        CandlestickDataBuilder().with_price_range(50000, 50100).build(),
        CandlestickDataBuilder().with_price_range(50100, 49900).build(),
        CandlestickDataBuilder().with_price_range(49900, 50050).build(),
    ],
    'high_volatility': [
        CandlestickDataBuilder().with_price_range(50000, 50000).with_high_volatility().build(),
        CandlestickDataBuilder().with_price_range(50000, 50000).with_high_volatility().build(),
    ]
}