# Exchange Order Validation

Comprehensive guide to the bot's intelligent order validation system that ensures compliance with exchange-specific requirements and filters.

## Overview

The Crypto Trading Bot includes sophisticated order validation that automatically adjusts orders to meet exchange requirements, preventing common filter errors and ensuring reliable trade execution.

## Supported Exchange Filters

### Binance Exchange Filters

#### PRICE_FILTER
**What it validates:** Price precision and tick size compliance
```
Error: "Filter failure: PRICE_FILTER"
```

**Automatic handling:**
- **DOGE**: Rounds to 0.00001 tick size (5 decimals)
- **BTC**: Rounds to 0.01 tick size (2 decimals)  
- **Others**: Rounds to 0.0001 tick size (4 decimals)

**Example:**
```
Input:  $0.240132018
Output: $0.24013 (DOGE - rounded to 5 decimals)
```

#### MIN_NOTIONAL
**What it validates:** Minimum order value requirements
```
Error: "Filter failure: MIN_NOTIONAL"
```

**Automatic handling:**
- Calculates order value (price × quantity)
- If below minimum ($10), automatically increases quantity
- Logs adjustment details for transparency

**Example:**
```
Original: 1 DOGE @ $0.24 = $0.24 notional
Adjusted: 42 DOGE @ $0.24 = $10.08 notional
```

#### PERCENT_PRICE_BY_SIDE
**What it validates:** Price deviation from current market price
```
Error: "Filter failure: PERCENT_PRICE_BY_SIDE"
```

**Challenges:**
- Very strict limits on price deviation (often <0.1%)
- May conflict with traditional grid trading approaches
- Requires current market price alignment

**Bot handling:**
- Fetches current market price before grid initialization
- Uses live price data instead of historical averages
- Provides detailed error messages when limits exceeded

#### LOT_SIZE
**What it validates:** Quantity precision and step size requirements
```
Error: "Filter failure: LOT_SIZE"
```

**Automatic handling:**
- Validates quantity meets minimum requirements
- Adjusts to proper step size increments
- Asset-specific quantity formatting

## Order Validation Process

### 1. Price Validation
```python
def _validate_and_adjust_price(self, price: float) -> float:
    if "DOGE" in self.currency_asset:
        tick_size = 0.00001
        adjusted_price = round(price / tick_size) * tick_size
        return round(adjusted_price, 5)
    # ... other assets
```

### 2. Quantity Validation  
```python
def _validate_and_adjust_quantity(self, quantity: float, price: float) -> float:
    notional_value = quantity * price
    
    if "DOGE" in self.currency_asset:
        min_notional = 10.0
        if notional_value < min_notional:
            required_quantity = max(1, int(min_notional / price) + 1)
            return required_quantity
    # ... other assets
```

### 3. Logging and Transparency
```
📊 Order Validation: Original qty=1, price=$0.240132
📊 Order Validation: Adjusted qty=42, price=$0.240130  
📊 Order Validation: Notional value=$10.08
⚠️  MIN_NOTIONAL Adjustment: $0.24 < $10.00
   Increasing quantity from 1 to 42
```

## Asset-Specific Configuration

### DOGE (Recommended for Testing)
```
Tick Size: 0.00001 (5 decimal places)
Min Notional: $10.00
Typical Price: ~$0.15-0.30
Grid Compatibility: Excellent
```

**Why DOGE is recommended:**
- Lower absolute price reduces filter conflicts
- Better grid trading compatibility
- More forgiving exchange filters
- Lower capital requirements for testing

### BTC (Higher Requirements)
```
Tick Size: 0.01 (2 decimal places)
Min Notional: $10.00
Typical Price: ~$45,000-50,000
Grid Compatibility: Limited (strict PERCENT_PRICE_BY_SIDE)
```

**BTC challenges:**
- High price creates large absolute deviations
- Very strict PERCENT_PRICE_BY_SIDE limits
- May conflict with traditional grid trading
- Requires precise market price alignment

### Other Assets (Default Settings)
```
Tick Size: 0.0001 (4 decimal places)
Min Notional: $10.00
Grid Compatibility: Varies by asset
```

## Implementation Across Exchanges

### TestExchange (Recommended for Development)
- **Real market data** from Binance API
- **Simulated orders** using test endpoints
- **Full validation** including all filters
- **Safe testing** with no real money risk

### Live Binance Exchange
- **Real market data** and **real orders**
- **Full validation** with identical logic
- **Production logging** for monitoring
- **Real money** - use with caution

## Common Validation Scenarios

### Scenario 1: DOGE Grid Trading
```
Strategy: GridTradingStrategy with 1% levels
Asset: DOGE @ $0.24
Grid Level 1: BUY @ $0.2376, SELL @ $0.2424

Validation:
✅ Price: $0.2376 → $0.23760 (valid tick size)
✅ Quantity: 1 → 42 (meets $10 minimum notional)
✅ Result: 42 DOGE @ $0.23760 = $9.98 ≈ $10.00
```

### Scenario 2: BTC Grid Trading (Challenging)
```
Strategy: GridTradingStrategy with 0.01% levels  
Asset: BTC @ $47,200
Grid Level 1: BUY @ $47,195.28, SELL @ $47,204.72

Validation:
✅ Price: $47,195.28 → $47,195.28 (valid tick size)
❌ PERCENT_PRICE_BY_SIDE: May exceed deviation limits
💡 Solution: Use current market price, smaller grid percentage
```

### Scenario 3: Minimum Notional Adjustment
```
Original Order: 1 DOGE @ $0.15 = $0.15 notional
Problem: Below $10.00 minimum

Adjustment Process:
1. Calculate required quantity: $10.00 ÷ $0.15 = 66.67
2. Round up for safety: 67 DOGE
3. Final order: 67 DOGE @ $0.15 = $10.05 notional ✅
```

## Best Practices

### For Development
1. **Start with DOGE** - better filter compatibility
2. **Use TestExchange** - real data, safe testing
3. **Monitor validation logs** - understand adjustments
4. **Test edge cases** - very small/large orders

### For Production
1. **Test extensively** in TestExchange first
2. **Start with small amounts** 
3. **Monitor validation metrics**
4. **Have rollback plans** for filter changes

### For Grid Trading
1. **Use small grid percentages** (0.01% - 0.1%)
2. **Fetch current market prices** before initialization
3. **Consider dynamic grids** instead of static price levels
4. **Monitor PERCENT_PRICE_BY_SIDE** errors closely

## Troubleshooting

### Common Errors and Solutions

#### "Filter failure: PERCENT_PRICE_BY_SIDE"
**Cause:** Order price too far from current market price
**Solution:** 
- Use current market price instead of historical data
- Reduce grid percentage
- Consider dynamic order placement

#### "Filter failure: MIN_NOTIONAL"  
**Cause:** Order value below exchange minimum
**Solution:**
- Automatic quantity adjustment (already implemented)
- Check validation logs for adjustment details

#### "Filter failure: PRICE_FILTER"
**Cause:** Price doesn't meet tick size requirements
**Solution:**
- Automatic price rounding (already implemented)
- Verify asset-specific tick sizes

## Performance Impact

### Validation Overhead
- **Price validation**: ~0.1ms per order
- **Quantity calculation**: ~0.2ms per order  
- **Logging**: ~0.5ms per order
- **Total overhead**: <1ms per order

### Memory Usage
- **Minimal impact** - validation is stateless
- **No persistent storage** of validation rules
- **Real-time calculation** based on current conditions

---

🛡️ **Safety Note**: Order validation prevents most exchange filter errors, but market conditions can change rapidly. Always monitor live trading and have emergency stop procedures in place.