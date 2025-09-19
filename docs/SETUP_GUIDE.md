# 🚀 Comprehensive Setup Guide

This guide covers everything you need to know about setting up and working with the Crypto Trading Bot project.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Virtual Environment Setup](#virtual-environment-setup)
3. [Dependencies](#dependencies)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.12+** (recommended, minimum 3.9)
- **Git** for version control
- **Code editor** (VS Code recommended)
- **API access** to supported exchanges (for live trading)

## Virtual Environment Setup

### Why Use Virtual Environments?

Virtual environments provide:
- **Isolated dependencies** - No conflicts with other projects
- **Reproducible builds** - Everyone gets the same package versions
- **Clean development** - Easy to reset or recreate environment

### Creating and Activating

```bash
# 1. Navigate to project directory
cd /path/to/Crypto-Trading-Bot

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# 4. Verify activation
python --version  # Should show Python 3.12.x
which python      # Should point to .venv/bin/python
```

### Visual Confirmation

When activated, your terminal prompt should show:
```bash
(.venv) username@computer:~/Crypto-Trading-Bot$
```

### Deactivating (when needed)

```bash
deactivate
```

## Dependencies

### Installation

With virtual environment activated:

```bash
# Install all project dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep pytest  # Should show pytest and related packages
```

### Dependency Categories

Our `requirements.txt` is organized into sections:

- **Core Dependencies**: Essential for trading functionality
- **Testing Framework**: pytest, coverage, mocking tools
- **Development Tools**: Enhanced test output, debugging aids
- **Optional Data Science**: jupyter, matplotlib for analysis

### Troubleshooting Dependencies

If you encounter issues:

```bash
# Upgrade pip first
pip install --upgrade pip

# Clean install
pip install --force-reinstall -r requirements.txt

# Check for conflicts
pip check
```

## Configuration

### Environment File Setup

```bash
# 1. Copy example configuration
cp .env.example .env

# 2. Edit with your settings
code .env  # or nano .env

# 3. Validate configuration
python validate_env.py
```

### Key Configuration Options

```env
# Trading Mode
MODE="backtest"  # Safe for testing
# MODE="trade"   # Live trading (requires real API keys)

# Exchange Selection
EXCHANGE="BinanceBacktestClient"  # For backtesting
# EXCHANGE="Binance"              # For live trading

# API Credentials (live trading only)
API_KEY="your_api_key_here"
API_SECRET="your_secret_here"
```

## Verification

### Quick Health Check

```bash
# With virtual environment activated

# 1. Python environment
python --version
python -c "import sys; print('Python path:', sys.executable)"

# 2. Dependencies
python -c "import pytest; print('pytest:', pytest.__version__)"
python -c "import pandas; print('pandas:', pandas.__version__)"

# 3. Project imports
python -c "from Strategies.GridTradingStrategy import GridTradingStrategy; print('Strategy import: OK')"

# 4. Configuration
python validate_env.py
```

### Test Suite

```bash
# Run all tests
python -m pytest Tests/ -v

# Run specific modules
python -m pytest Tests/unit/strategies/ -v

# Run with coverage
python build.py --coverage
```

## Common Workflows

### Daily Development Workflow

```bash
# 1. Navigate and activate
cd /path/to/Crypto-Trading-Bot
source .venv/bin/activate

# 2. Pull latest changes
git pull origin main

# 3. Update dependencies (if requirements.txt changed)
pip install -r requirements.txt

# 4. Run tests before making changes
python -m pytest Tests/ -q

# 5. Make your changes...

# 6. Test your changes
python -m pytest Tests/unit/strategies/ -v
python build.py --coverage

# 7. Commit and push
git add .
git commit -m "Your descriptive message"
git push origin your-branch
```

### Running Different Components

```bash
# Main trading bot
python main.py BTC_USD

# Coverage analysis
python build.py --coverage

# Build verification
python build.py --all

# Fee collection analysis
cd Collect-Fees
python run.py
```

### Testing Specific Features

```bash
# Strategy testing
python -m pytest Tests/unit/strategies/grid_trading_strategy_complete_test.py -v

# Exchange testing
python -m pytest Tests/unit/exchanges/ -v

# Integration tests
python -m pytest Tests/integration/ -v
```

## Troubleshooting

### Common Issues

#### 1. Virtual Environment Not Active
**Symptoms**: `ModuleNotFoundError` for project dependencies
**Solution**: 
```bash
source .venv/bin/activate
```

#### 2. Python Version Mismatch
**Symptoms**: Syntax errors, feature not available
**Solution**:
```bash
python --version  # Check current version
# Recreate virtual environment with correct Python version
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Dependency Conflicts
**Symptoms**: Import errors, version conflicts
**Solution**:
```bash
pip install --force-reinstall -r requirements.txt
pip check  # Verify no conflicts
```

#### 4. Test Failures
**Symptoms**: Tests failing unexpectedly
**Solution**:
```bash
# Clean test cache
rm -rf .pytest_cache/
python -m pytest Tests/ -v --tb=short
```

#### 5. Coverage Issues
**Symptoms**: Coverage reports not generating
**Solution**:
```bash
# Check coverage configuration
cat pyproject.toml | grep -A 10 "\[tool.coverage"
python build.py --coverage
```

### Environment Debugging

```bash
# Check Python environment
python -c "
import sys
print('Python executable:', sys.executable)
print('Python version:', sys.version)
print('Python path:', sys.path)
"

# Check installed packages
pip list

# Check project structure
find . -name "*.py" | head -10
```

### Getting Help

1. **Check logs**: Look in `logs/` directory for detailed error information
2. **Validate setup**: Run `python validate_env.py`
3. **Review documentation**: Check other files in `docs/` folder
4. **Test environment**: Run `python build.py --test`

## 📚 Additional Resources

- [Testing Guide](TESTING.md) - Comprehensive testing documentation
- [Metrics Guide](METRICS.md) - Performance monitoring and metrics
- [Build Guide](BUILD_README.md) - Build system and automation
- [Build Organization](BUILD_ORGANIZATION.md) - Project structure details

---

💡 **Pro Tip**: Always work with the virtual environment activated. If you see `(.venv)` in your prompt, you're good to go!