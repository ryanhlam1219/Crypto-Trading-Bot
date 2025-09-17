#!/bin/bash

# Crypto Trading Bot Setup Script
# This script helps you set up the environment configuration

echo "🚀 Crypto Trading Bot Setup"
echo "============================"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    echo "   Do you want to overwrite it? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Your existing .env file was preserved."
        exit 0
    fi
fi

# Copy example file
if [ ! -f ".env.example" ]; then
    echo "❌ Error: .env.example file not found!"
    echo "   Please make sure you're in the correct directory."
    exit 1
fi

cp .env.example .env
echo "✅ Created .env file from .env.example"
echo ""

# Prompt for API credentials
echo "🔑 API Credentials Setup"
echo "========================"
echo "Enter your exchange API credentials:"
echo "(You can find these in your exchange account settings)"
echo ""

echo "Enter your API Key:"
read -r api_key

echo "Enter your API Secret:"
read -r -s api_secret
echo ""

# Update the .env file
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/YOUR_API_KEY_HERE/$api_key/g" .env
    sed -i '' "s/YOUR_API_SECRET_HERE/$api_secret/g" .env
else
    # Linux
    sed -i "s/YOUR_API_KEY_HERE/$api_key/g" .env
    sed -i "s/YOUR_API_SECRET_HERE/$api_secret/g" .env
fi

echo "✅ API credentials updated in .env file"
echo ""

# Trading mode selection
echo "🎯 Trading Mode Setup"
echo "===================="
echo "Choose your trading mode:"
echo "1) backtest  - Test strategies with historical data (SAFE)"
echo "2) test      - Live data with simulated trades (SAFE)"  
echo "3) real      - Live trading with real money (CAUTION!)"
echo ""
echo "Enter your choice (1-3) [default: 1]:"
read -r mode_choice

case $mode_choice in
    2)
        trading_mode="test"
        mode="trade"
        exchange="TestExchange"
        ;;
    3)
        trading_mode="real"
        mode="trade"
        exchange="Binance"
        echo ""
        echo "⚠️  WARNING: You selected REAL trading mode!"
        echo "   This will use real money. Are you sure? (y/N)"
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo "Switching to backtest mode for safety."
            trading_mode="test"
            mode="backtest"
            exchange="BinanceBacktestClient"
        fi
        ;;
    *)
        trading_mode="test"
        mode="backtest"
        exchange="BinanceBacktestClient"
        ;;
esac

# Update trading mode in .env
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/MODE=\"backtest\"/MODE=\"$mode\"/g" .env
    sed -i '' "s/TRADING_MODE=\"test\"/TRADING_MODE=\"$trading_mode\"/g" .env
    sed -i '' "s/EXCHANGE=\"Binance\"/EXCHANGE=\"$exchange\"/g" .env
else
    # Linux
    sed -i "s/MODE=\"backtest\"/MODE=\"$mode\"/g" .env
    sed -i "s/TRADING_MODE=\"test\"/TRADING_MODE=\"$trading_mode\"/g" .env
    sed -i "s/EXCHANGE=\"Binance\"/EXCHANGE=\"$exchange\"/g" .env
fi

echo "✅ Trading mode configured: $mode ($trading_mode)"
echo ""

# Installation check
echo "📦 Dependency Check"
echo "==================="
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found: $(python3 --version)"
    
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies..."
        python3 -m pip install -r requirements.txt
        echo "✅ Dependencies installed"
    else
        echo "⚠️  requirements.txt not found"
    fi
else
    echo "❌ Python3 not found. Please install Python 3.9+ first."
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "Your crypto trading bot is ready to use!"
echo ""
echo "Next steps:"
echo "1. Review your .env configuration"
echo "2. Test with: python3 main.py BTC_USD"
echo "3. Check the README.md for more details"
echo ""
echo "💡 Pro tip: Always start with backtest mode to test your strategies!"
echo ""
echo "🔒 Security reminder:"
echo "   - Never share your API keys"
echo "   - Keep your .env file private"
echo "   - Start with small amounts for live trading"
