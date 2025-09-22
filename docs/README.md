# 📚 Documentation Index

Welcome to the Crypto Trading Bot documentation! This folder contains all detailed guides and references for the project.

## 🚀 Getting Started

**New to the project?** Start here:

1. **[Setup Guide](SETUP_GUIDE.md)** - Complete setup instructions including virtual environment, dependencies, and configuration
2. **[Main README](../README.md)** - Project overview and quick start guide

## 📖 Detailed Guides

### Development & Testing
- **[Testing Guide](TESTING.md)** - Comprehensive testing documentation, test organization, and best practices
- **[Build Guide](BUILD_README.md)** - Build system, automation scripts, and coverage analysis
- **[Build Organization](BUILD_ORGANIZATION.md)** - Project structure and organization details

### Configuration & Setup
- **[Configuration Guide](CONFIGURATION.md)** - Complete API setup, environment variables, and network requirements
- **[Exchange Validation Guide](EXCHANGE_VALIDATION.md)** - Order validation, filter compliance, and asset-specific requirements

### Monitoring & Analysis
- **[Metrics Guide](METRICS.md)** - Performance monitoring, metrics collection, and analysis tools with optimization details

## 🗂️ Documentation Organization

```
docs/
├── README.md              # This index file
├── SETUP_GUIDE.md         # Complete setup instructions
├── CONFIGURATION.md       # API setup and environment variables
├── TESTING.md             # Testing framework and practices
├── METRICS.md             # Performance monitoring
├── BUILD_README.md        # Build system documentation
└── BUILD_ORGANIZATION.md  # Project structure details
```

## 🔍 Quick Reference

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Common Commands
```bash
# Run tests
python -m pytest Tests/ -v

# Generate coverage
python build.py --coverage

# Run main bot
python main.py BTC_USD
```

### Key Configuration Files
- `requirements.txt` - All project dependencies
- `pyproject.toml` - pytest and coverage configuration
- `.env` - Environment variables and API credentials
- `build.py` - Main build and test automation script

## 🆘 Need Help?

1. **Setup Issues**: See [Setup Guide](SETUP_GUIDE.md#troubleshooting)
2. **Testing Problems**: Check [Testing Guide](TESTING.md)
3. **Build Failures**: Review [Build Guide](BUILD_README.md)
4. **Environment Validation**: Run `python validate_env.py`

## 📝 Contributing to Documentation

When adding new documentation:

1. **Place files in `docs/`** folder
2. **Update this index** with new file references
3. **Use clear titles** and consistent formatting
4. **Include examples** and code snippets
5. **Cross-reference** related documents

---

💡 **Tip**: Keep the main README simple and link to detailed guides in this docs folder!