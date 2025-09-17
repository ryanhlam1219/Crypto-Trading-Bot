#!/usr/bin/env python3
"""
Environment Configuration Validator
Checks if your .env file is properly configured for the Crypto Trading Bot
"""

import os
import sys
from decouple import config, UndefinedValueError

def validate_env():
    """Validate the .env configuration"""
    print("🔍 Validating .env configuration...")
    print("=" * 40)
    
    # Required configuration keys
    required_keys = {
        'EXCHANGE': 'Exchange selection',
        'AVAILABLE_EXCHANGES': 'Available exchanges list',
        'MODE': 'Trading mode (backtest/trade)',
        'STRATEGY': 'Trading strategy',
        'TRADING_MODE': 'Trading execution mode (test/real)',
        'CANDLE_INTERVAL': 'Candlestick interval',
        'CURRENCY': 'Base currency',
        'ASSET': 'Quote currency',
        'API_KEY': 'Exchange API key',
        'API_SECRET': 'Exchange API secret',
        'TRADE_INTERVAL': 'Trade check interval'
    }
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Run './setup.sh' or copy '.env.example' to '.env'")
        return False
    
    errors = []
    warnings = []
    
    # Validate each required key
    for key, description in required_keys.items():
        try:
            value = config(key)
            
            # Check for placeholder values
            if key in ['API_KEY', 'API_SECRET']:
                if value in ['YOUR_API_KEY_HERE', 'YOUR_API_SECRET_HERE', '']:
                    warnings.append(f"⚠️  {key}: Still contains placeholder value")
                else:
                    print(f"✅ {key}: Configured")
            else:
                print(f"✅ {key}: {value}")
                
        except UndefinedValueError:
            errors.append(f"❌ {key}: Missing ({description})")
    
    # Print any errors
    if errors:
        print("\n🚨 Configuration Errors:")
        for error in errors:
            print(f"   {error}")
    
    # Print any warnings  
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   {warning}")
        print("   💡 Make sure to replace placeholder values with your actual API credentials")
    
    # Validate trading mode combinations
    try:
        mode = config('MODE')
        trading_mode = config('TRADING_MODE') 
        exchange = config('EXCHANGE')
        
        print(f"\n🎯 Configuration Summary:")
        print(f"   Mode: {mode}")
        print(f"   Trading Mode: {trading_mode}")
        print(f"   Exchange: {exchange}")
        
        # Provide recommendations
        if mode == 'backtest':
            if not exchange.endswith('BacktestClient'):
                warnings.append("💡 For backtesting, consider using BinanceBacktestClient or KrakenBacktestClient")
        elif mode == 'trade' and trading_mode == 'real':
            print(f"   ⚠️  CAUTION: Real trading mode enabled!")
            if config('API_KEY') in ['YOUR_API_KEY_HERE', '']:
                errors.append("❌ Real trading requires valid API credentials")
    
    except Exception as e:
        errors.append(f"❌ Configuration validation error: {e}")
    
    # Final status
    print("\n" + "=" * 40)
    if errors:
        print("❌ Configuration validation FAILED")
        print("   Please fix the errors above before running the bot")
        return False
    elif warnings:
        print("⚠️  Configuration validation PASSED with warnings")
        print("   The bot will run, but consider addressing the warnings")
        return True
    else:
        print("✅ Configuration validation PASSED")
        print("   Your bot is ready to run!")
        return True

def main():
    """Main function"""
    print("🚀 Crypto Trading Bot - Environment Validator")
    print()
    
    if not validate_env():
        sys.exit(1)
    
    print("\n💡 Next steps:")
    print("   1. Test your bot: python3 main.py BTC_USD")
    print("   2. Check the README.md for more information")
    print("   3. Start with backtest mode to test strategies safely")

if __name__ == "__main__":
    main()
