# 💰 Fee Collection System

A comprehensive trading fee analysis tool that monitors and compares fees across multiple cryptocurrency exchanges.

## 🎯 What It Does

This system continuously collects real-time trading fee data from multiple exchanges to help you:
- **Compare fees** across different exchanges
- **Track fee changes** over time
- **Calculate fee ratios** for arbitrage opportunities
- **Analyze transaction costs** at different volume levels

## 🏗️ Architecture

```
Collect-Fees/
├── exchanges/              # Exchange-specific fee collectors
│   ├── binance_collector.py    # Binance.US fee data
│   ├── kraken_collector.py     # Kraken fee data
│   ├── gemini_collector.py     # Gemini fee data
│   └── coinbase_collector.py   # Coinbase Pro fee data
├── data/                   # Historical fee data storage
├── logs/                   # Runtime logs (auto-generated)
├── config.py              # Configuration management
├── fee_collector.py       # Main collection orchestrator
├── ratio_calculator.py    # Fee ratio analysis
└── run.py                 # Entry point
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file with your exchange API credentials:
```env
# Exchange API Keys (add only the exchanges you want to monitor)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret

KRAKEN_API_KEY=your_kraken_api_key  
KRAKEN_API_SECRET=your_kraken_secret

GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_SECRET=your_gemini_secret

# Trading pair to monitor
BASE_CURRENCY=BTC
QUOTE_CURRENCY=USD

# Collection interval (seconds)
COLLECTION_INTERVAL_SECONDS=300
```

### 3. Run the Collector
```bash
python3 run.py
```

## 📊 How It Works

### Fee Collection Process
1. **Connect** to configured exchanges via their APIs
2. **Fetch** current trading fees for the specified pair
3. **Calculate** fees at different transaction volumes
4. **Store** data with timestamps for historical analysis
5. **Repeat** at configured intervals

### Ratio Analysis
The system calculates fee ratios between exchanges to identify:
- **Arbitrage opportunities** where fee differences exceed transfer costs
- **Optimal routing** for trades based on transaction size
- **Historical trends** in fee competitiveness

### Transaction Volume Analysis
Tests fee calculations across multiple transaction sizes:
- Starts from minimum trade size (0.001 × coin price)
- Doubles incrementally: 0.002, 0.004, 0.008, etc.
- Continues up to 10× the coin price
- Provides comprehensive fee mapping across volume ranges

## 📈 Data Output

### Fee Data Structure
```json
{
  "timestamp": "2025-09-17T16:30:00Z",
  "exchange": "binance",
  "symbol": "BTCUSD", 
  "transaction_amount": 1000.00,
  "fee_usd": 1.50,
  "fee_percentage": 0.15,
  "price": 45000.00
}
```

### Ratio Analysis
```json
{
  "timestamp": "2025-09-17T16:30:00Z",
  "exchange_pair": "binance_vs_kraken",
  "ratio": 1.25,
  "fee_difference": 0.05,
  "arbitrage_opportunity": true
}
```

## ⚙️ Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `BASE_CURRENCY` | Asset to trade (BTC, ETH, etc.) | BTC |
| `QUOTE_CURRENCY` | Currency to price in (USD, EUR, etc.) | USD |
| `COLLECTION_INTERVAL_SECONDS` | Time between collections | 300 |
| `LOG_LEVEL` | Logging verbosity | INFO |

## 🔒 Security Notes

- **Read-only permissions**: Only requires API keys with read access
- **No trading**: System only queries fee information, never places orders
- **Local storage**: All data stored locally in the `data/` directory
- **Environment variables**: Keep API keys in `.env` file (never commit to git)

## 📋 Requirements

- Python 3.9+
- Exchange API keys (read-only permissions sufficient)
- Internet connection for API access

## 🔧 Troubleshooting

### No Data Collected
- Check that API keys are correctly configured in `.env`
- Verify API keys have read permissions
- Check logs in `logs/` directory for error details

### Exchange Connection Errors
- Verify exchange API endpoints are accessible
- Check if your IP is whitelisted (if required by exchange)
- Ensure API rate limits aren't exceeded

### Configuration Issues
```bash
# Test configuration
python3 -c "from config import Config; print(Config.validate_config())"
```

## 📊 Example Usage

Monitor BTC/USD fees across all exchanges:
```bash
# Set environment
export BASE_CURRENCY=BTC
export QUOTE_CURRENCY=USD

# Run collector
python3 run.py
```

Analyze ETH/USD with custom interval:
```bash
export BASE_CURRENCY=ETH
export QUOTE_CURRENCY=USD
export COLLECTION_INTERVAL_SECONDS=600

python3 run.py
```

---

**Note**: This tool is for analysis purposes only. Always verify fee calculations with exchange documentation before making trading decisions.                                                                     