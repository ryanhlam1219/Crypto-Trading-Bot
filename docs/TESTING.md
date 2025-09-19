# Unit Testing Guide for Crypto Trading Bot

## Overview

This unit testing implementation provides comprehensive coverage for ensuring all Exchange and Strategy implementations comply with their base class interfaces. The testing framework will catch compliance issues before they cause runtime errors.

## Key Benefits

1. **Interface Compliance**: Ensures all Exchange/Strategy implementations follow the required contracts
2. **Regression Prevention**: Catches breaking changes during development
3. **Documentation**: Tests serve as living documentation of expected behavior
4. **Confidence**: Allows safe refactoring and new feature development

## Test Structure

```
Tests/
├── unit/                          # Unit tests
│   ├── exchanges/                 # Exchange-specific tests
│   │   ├── binance_complete_test.py      # Comprehensive Binance tests
│   │   ├── kraken_test.py               # Kraken implementation tests
│   │   └── backtest_clients_test.py     # Backtest client tests
│   ├── strategies/                # Strategy-specific tests
│   │   ├── grid_trading_strategy_complete_test.py  # Consolidated comprehensive tests (29 tests, 85% coverage)
│   │   └── exchange_models_test.py             # Exchange models tests
│   ├── utils/                     # Utility class tests
│   │   ├── metrics_collector_test.py       # MetricsCollector tests
│   │   ├── metrics_collector_edge_cases_test.py  # Edge case tests
│   │   └── utils_test.py                   # General utils tests
│   └── compliance/                # Compliance tests
│       └── compliance_test.py     # Interface compliance tests
├── integration/                   # Integration tests
│   ├── integration_test.py        # End-to-end integration tests
│   └── live_exchanges_integration_test.py  # Live exchange integration
├── fixtures/                      # Test data and mocks
│   ├── exchange_mocks.py          # Exchange test data
│   └── strategy_mocks.py          # Strategy test data
└── conftest.py                    # Shared pytest configuration
```

## Running Tests

### Install Dependencies
```bash
python run_tests.py install
```

### Run All Tests
```bash
python run_tests.py all
```

### Run Specific Test Categories
```bash
python run_tests.py compliance    # Interface compliance tests
python run_tests.py exchange      # Exchange implementation tests
python run_tests.py strategy      # Strategy implementation tests
python run_tests.py utils         # Utility class tests
```

### Generate Coverage Report

The testing framework now supports two distinct coverage modes:

#### Focused Module Coverage
Test specific modules with detailed coverage analysis:
```bash
# GridTradingStrategy focused testing (85% coverage)
pytest Tests/unit/strategies/grid_trading_strategy_complete_test.py --cov=Strategies.GridTradingStrategy --cov-report=term-missing -v

# Exchange focused testing
pytest Tests/unit/exchanges/ --cov=Exchanges --cov-report=term-missing -v

# Utils focused testing  
pytest Tests/unit/utils/ --cov=Utils --cov-report=term-missing -v
```

#### Full Project Coverage
Test all modules together with comprehensive coverage:
```bash
# All modules together (68% overall coverage)
pytest Tests/ --cov=Exchanges --cov=Strategies --cov=Utils --cov-report=term-missing -q

# Or use the automated build system
python build.py --coverage
python build.py --all
```

#### Coverage Configuration Notes
- **pyproject.toml** contains default source configuration for all modules
- **Command-line --cov arguments** override defaults for focused testing
- **build.py --all** uses comprehensive coverage across Exchanges, Strategies, and Utils
- **Individual module testing** allows for detailed analysis without dilution

## Core Compliance Tests

### Exchange Compliance (`compliance_test.py`)

The most important tests for your needs - these verify every Exchange implementation:

- **Inherits from Exchange base class**
- **Implements all abstract methods**
- **Has proper method signatures**
- **Can be instantiated with standard parameters**
- **Has required class attributes (api_url)**

### Strategy Compliance (`compliance_test.py`)

Verifies every Strategy implementation:

- **Inherits from Strategy base class**
- **Implements all abstract methods**
- **Integrates properly with MetricsCollector**
- **Has proper method signatures**
- **Maintains required instance attributes**

## Adding New Implementations

When you add a new Exchange or Strategy, simply add it to the test lists in `compliance_test.py`:

### New Exchange
```python
# In Tests/unit/compliance/compliance_test.py
EXCHANGE_IMPLEMENTATIONS = [
    ('Exchanges.Live.Binance', 'Binance'),
    ('Exchanges.Live.YourNewExchange', 'YourNewExchange'),  # Add here
    # ... existing entries
]
```

### New Strategy
```python
# In Tests/unit/compliance/compliance_test.py  
STRATEGY_IMPLEMENTATIONS = [
    ('Strategies.GridTradingStrategy', 'GridTradingStrategy'),
    ('Strategies.YourNewStrategy', 'YourNewStrategy'),  # Add here
    # ... existing entries
]
```

The parametrized tests will automatically verify your new implementation complies with all interface requirements.

## Test Categories by Priority

### 1. Critical (Must Pass Before Deployment)
- `compliance_test.py` - Interface compliance
- Base class tests (`test_exchange_base.py`, `test_strategy_base.py`)

### 2. Important (Should Pass for Quality)
- Implementation-specific tests
- MetricsCollector integration tests

### 3. Helpful (Good for Development)
- Mock data validation
- Error handling scenarios
- Performance tests

## Common Test Patterns

### Exchange Implementation Test
```python
def test_my_exchange_compliance():
    """Test MyExchange meets all requirements."""
    from Exchanges.Live.MyExchange import MyExchange
    
    compliance = TestExchangeComplianceChecks.verify_exchange_compliance(MyExchange)
    assert all(compliance.values()), f"Failed: {compliance}"
```

### Strategy Implementation Test
```python
def test_my_strategy_compliance():
    """Test MyStrategy meets all requirements."""
    from Strategies.MyStrategy import MyStrategy
    
    compliance = TestStrategyComplianceChecks.verify_strategy_compliance(MyStrategy)
    assert all(compliance.values()), f"Failed: {compliance}"
```

## Mock Data and Fixtures

### Exchange Mocks (`fixtures/exchange_mocks.py`)
- Standard API responses for different exchanges
- Error scenarios and edge cases
- Candlestick data builders

### Strategy Mocks (`fixtures/strategy_mocks.py`)
- Mock trading scenarios
- Price movement patterns
- MetricsCollector mocks

## Continuous Integration

The tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Unit Tests
  run: |
    python run_tests.py install
    python run_tests.py all
    python run_tests.py coverage
```

## Debugging Test Failures

### Exchange Compliance Failure
```
ExchangeComplianceError: BinanceExchange failed compliance checks: implements_all_abstract_methods
```
**Solution**: Implement missing abstract methods in your Exchange class.

### Strategy Compliance Failure
```
StrategyComplianceError: MyStrategy failed compliance checks: metrics_collector_integration
```
**Solution**: Ensure your Strategy properly uses the MetricsCollector parameter.

### Import Errors
```
ImportError: Could not import MyExchange from Exchanges.Live.MyExchange
```
**Solution**: Check module path and class name in `EXCHANGE_IMPLEMENTATIONS`.

## Test File Naming Convention

### Standard Naming Pattern
All test files should use the **suffix** convention for better readability:

✅ **Correct**: `*_test.py`
- `grid_trading_strategy_test.py`
- `binance_exchange_test.py` 
- `metrics_collector_test.py`
- `compliance_test.py`

❌ **Avoid**: `test_*.py`
- `test_grid_trading_strategy.py`
- `test_binance_exchange.py`
- `test_metrics_collector.py`

### Benefits of Suffix Convention
- **Better Readability**: Module name comes first, making it clear what's being tested
- **Logical Grouping**: Related tests appear together when sorted alphabetically
- **IDE Support**: Better autocompletion and navigation
- **Consistent Structure**: Matches the module hierarchy more naturally

### Examples by Category
```
Tests/unit/strategies/
├── grid_trading_strategy_complete_test.py  # Consolidated comprehensive tests (29 tests, 85% coverage)
└── exchange_models_test.py                 # Model validation tests

Tests/unit/exchanges/
├── binance_complete_test.py                # Comprehensive Binance tests
├── kraken_test.py                         # Kraken implementation tests
└── backtest_clients_test.py               # Backtest client tests

Tests/unit/utils/
├── metrics_collector_test.py              # MetricsCollector core tests
├── metrics_collector_edge_cases_test.py   # Edge case and error handling tests
└── utils_test.py                          # General utility tests
```

## Best Practices

1. **Run compliance tests first** when developing new implementations
2. **Add implementation-specific tests** for complex logic
3. **Use mock data** to avoid external API dependencies
4. **Test error scenarios** to ensure graceful failure handling
5. **Update test lists** when adding new implementations
6. **Follow naming convention**: Use `*_test.py` suffix for all test files

## Test Configuration

### pytest Configuration (`pyproject.toml`)
- Coverage thresholds
- Test discovery patterns
- Output formatting
- Marker definitions

### Shared Fixtures (`conftest.py`)
- Mock objects for common dependencies
- Sample data generators
- Test utilities

## Performance Considerations

- Tests use mocks to avoid network calls
- Large dataset tests verify memory efficiency
- Timeout protection for long-running tests
- Parallel execution support with pytest-xdist

## Extending Tests

### Custom Assertions
Add domain-specific assertions in test utility classes.

### New Test Categories
Create new test modules for specific functionality (e.g., `risk_management_test.py`).

### Integration Points
Tests can be extended to cover integration between components.

---

## Quick Start Checklist

✅ Install test dependencies: `python run_tests.py install`  
✅ Run all tests: `python run_tests.py all`  
✅ Check compliance: `python run_tests.py compliance`  
✅ **Test focused modules**: `pytest Tests/unit/strategies/grid_trading_strategy_complete_test.py --cov=Strategies.GridTradingStrategy --cov-report=term-missing -v`  
✅ **Test all modules**: `python build.py --all` or `pytest Tests/ --cov=Exchanges --cov=Strategies --cov=Utils --cov-report=term-missing -q`  
✅ Add new implementations to `compliance_test.py`  
✅ Run tests before committing changes  
✅ Aim for >90% code coverage per module  
✅ **Use dual coverage modes**: Focused testing for detailed analysis, comprehensive testing for overall health  

This testing framework ensures your trading bot remains reliable and maintainable as you add new exchanges and strategies!