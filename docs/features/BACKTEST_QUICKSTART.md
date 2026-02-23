# Backtesting System - Quick Start Guide

## For Backend Developers

### 1. Running the Service

```python
from backtest_service import BacktestService, BacktestConfig
from datetime import date, timedelta

# Create service
service = BacktestService()

# Create configuration
config = BacktestConfig(
    strategy_id="my_portfolio",
    initial_capital=10000,
    start_date=date(2020, 1, 1),
    end_date=date(2025, 1, 1),
    rebalance_frequency="monthly",
    benchmark="SPY",
    compositions=[
        {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.3}
    ]
)

# Run backtest
result = service.run_backtest(config)

# Access results
print(f"Total Return: {result.total_return_pct:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
print(f"Outperformance: {result.alpha:+.2f}%")
```

### 2. Testing the Service

```bash
# Run all backtest tests
pytest backend/tests/test_backtest_service.py -v

# Run specific test
pytest backend/tests/test_backtest_service.py::TestBacktestService::test_backtest_execution -v

# With coverage
pytest backend/tests/test_backtest_service.py --cov=backtest_service
```

### 3. Using the API

The API is already registered at `/api/backtest`. Start the server:

```bash
cd backend
python -m uvicorn main:app --reload
```

Then test endpoints:

```bash
# Run a backtest
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "test",
    "initial_capital": 10000,
    "rebalance_frequency": "monthly",
    "benchmark": "SPY",
    "compositions": [{"AAPL": 0.5, "MSFT": 0.5}]
  }'

# Get presets
curl http://localhost:8000/api/backtest/presets

# Get benchmarks
curl http://localhost:8000/api/backtest/benchmarks

# Get system stats
curl http://localhost:8000/api/backtest/stats
```

## For Frontend Developers

### 1. Using the Hook

```typescript
import { useBacktest } from '@/hooks/useBacktest';
import { BacktestConfig } from '@/types/backtest';
import { useEffect } from 'react';

export function MyComponent() {
  const {
    isLoading,
    error,
    result,
    presets,
    benchmarks,
    runBacktest,
    loadMetadata,
  } = useBacktest();

  // Load available options on mount
  useEffect(() => {
    loadMetadata();
  }, [loadMetadata]);

  // Run a backtest
  const handleTest = async () => {
    const config: BacktestConfig = {
      strategy_id: 'portfolio_1',
      initial_capital: 50000,
      rebalance_frequency: 'monthly',
      benchmark: 'SPY',
      compositions: [
        { ticker: 'AAPL', weight: 0.3 },
        { ticker: 'MSFT', weight: 0.4 },
        { ticker: 'GOOGL', weight: 0.3 },
      ],
      start_date: '2020-01-01',
      end_date: '2025-01-01',
    };

    const result = await runBacktest(config);
    if (result) {
      console.log(`Total Return: ${result.total_return_pct.toFixed(2)}%`);
    }
  };

  return (
    <div>
      <button onClick={handleTest} disabled={isLoading}>
        {isLoading ? 'Running...' : 'Run Backtest'}
      </button>
      {error && <div className="error">{error}</div>}
      {result && (
        <div>
          <h2>Results</h2>
          <p>Return: {result.annualized_return_pct.toFixed(2)}%</p>
          <p>Sharpe: {result.sharpe_ratio.toFixed(2)}</p>
        </div>
      )}
    </div>
  );
}
```

### 2. Using the BacktestPanel Component

```typescript
import { BacktestPanel } from '@/components/backtest';
import { CompositionItem } from '@/types/backtest';

export function StrategyPage() {
  const compositions: CompositionItem[] = [
    { ticker: 'AAPL', weight: 0.5 },
    { ticker: 'MSFT', weight: 0.5 },
  ];

  return (
    <div className="p-6">
      <BacktestPanel
        strategyId="my_strategy"
        compositions={compositions}
        onClose={() => console.log('Closed')}
      />
    </div>
  );
}
```

### 3. Displaying Metrics

```typescript
import { BacktestMetrics } from '@/components/backtest';
import { BacktestResult } from '@/types/backtest';

export function ResultsDisplay({ result }: { result: BacktestResult }) {
  return (
    <div>
      <h2>Backtest Results</h2>
      <BacktestMetrics result={result} />
    </div>
  );
}
```

### 4. Displaying Charts

```typescript
import { EquityCurveChart } from '@/components/backtest';
import { BacktestResult } from '@/types/backtest';

export function PerformanceChart({ result }: { result: BacktestResult }) {
  return (
    <div>
      <EquityCurveChart result={result} showDrawdown={true} />
    </div>
  );
}
```

## Common Use Cases

### 1. Testing a Simple Portfolio

```python
# Backend
config = BacktestConfig(
    strategy_id="simple_60_40",
    initial_capital=10000,
    start_date=date(2015, 1, 1),
    end_date=date(2025, 1, 1),
    rebalance_frequency="annual",
    benchmark="SPY",
    compositions=[
        {"SPY": 0.6, "AGG": 0.4}  # 60/40 stocks/bonds
    ]
)

result = service.run_backtest(config)
print(f"60/40 portfolio returned {result.total_return_pct:.2f}%")
print(f"vs SPY: {result.alpha:+.2f}%")
```

### 2. Testing Different Rebalancing Frequencies

```typescript
// Frontend
const frequencies = ['monthly', 'quarterly', 'annual'];

for (const freq of frequencies) {
  const result = await runBacktest({
    ...config,
    rebalance_frequency: freq,
  });
  console.log(`${freq}: ${result.total_return_pct.toFixed(2)}%`);
}
```

### 3. Comparing to Different Benchmarks

```typescript
// Frontend
const benchmarks = ['SPY', 'QQQ', 'VEA'];

for (const benchmark of benchmarks) {
  const result = await runBacktest({
    ...config,
    benchmark,
  });
  console.log(`vs ${benchmark}: ${result.alpha:+.2f}% alpha`);
}
```

### 4. Testing Different Time Periods

```typescript
// Frontend
const periods = [
  { label: '1Y', offset: 1 },
  { label: '3Y', offset: 3 },
  { label: '5Y', offset: 5 },
  { label: '10Y', offset: 10 },
];

for (const period of periods) {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - period.offset);

  const result = await runBacktest({
    ...config,
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
  });

  console.log(`${period.label}: ${result.annualized_return_pct.toFixed(2)}%`);
}
```

## Troubleshooting

### Issue: "Composition weights must sum to 1.0"

**Cause**: Weights don't add up to exactly 1.0

**Solution**:
```python
# Wrong
compositions = [{"AAPL": 0.3, "MSFT": 0.3}]  # Sums to 0.6

# Right
compositions = [{"AAPL": 0.5, "MSFT": 0.5}]  # Sums to 1.0
```

### Issue: "Backtest execution failed"

**Cause**: Could be missing data or other internal error

**Solution**:
```python
try:
    result = service.run_backtest(config)
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Execution error: {e}")
```

### Issue: No chart data displayed

**Cause**: Result has empty equity curve

**Solution**:
```typescript
if (result && result.equity_curve.length > 0) {
  return <EquityCurveChart result={result} />;
} else {
  return <p>No data available</p>;
}
```

## Performance Tips

1. **Use quarterly or annual rebalancing** for faster results with many assets
2. **Limit time period** to 10-20 years for quicker execution
3. **Cache results** if running same backtest multiple times
4. **Batch requests** if testing multiple configurations

## Next Steps

1. **Integrate into Strategy Page**
   - Add BacktestPanel to strategy detail view
   - Display results in modal or panel

2. **Add User Preferences**
   - Save favorite backtest configurations
   - Store test history

3. **Enable Data Export**
   - Export results to CSV
   - Generate PDF reports

4. **Add Advanced Features**
   - Monte Carlo simulations
   - Factor analysis
   - Tax-loss harvesting simulation

## File References

- **Backend Service**: `/backend/backtest_service.py`
- **API Routes**: `/backend/backtest_routes.py`
- **Frontend Hook**: `/frontend/hooks/useBacktest.ts`
- **Frontend Components**: `/frontend/components/backtest/`
- **Type Definitions**: `/frontend/types/backtest.ts`
- **Full Documentation**: `/BACKTEST_IMPLEMENTATION.md`
- **File Summary**: `/BACKTEST_FILES_CREATED.md`

## Testing Files

- **Service Tests**: `/backend/tests/test_backtest_service.py`
- **Route Tests**: `/backend/tests/test_backtest_routes.py`

Run with: `pytest backend/tests/test_backtest_*.py -v`

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/backtest/run` | Run a backtest |
| GET | `/api/backtest/presets` | Get time presets |
| GET | `/api/backtest/benchmarks` | Get benchmarks |
| GET | `/api/backtest/rebalance-frequencies` | Get rebalance options |
| GET | `/api/backtest/stats` | Get system stats |

## Support

For issues or questions:
1. Check `/BACKTEST_IMPLEMENTATION.md` for detailed documentation
2. Review test files for usage examples
3. Check error messages and traceback
4. See troubleshooting section above
