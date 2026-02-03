# MarketGPS Backtesting System

## Overview

A comprehensive backtesting engine for testing investment strategies against historical data. Users can simulate "What if I invested X years ago?" scenarios with their custom portfolio allocations.

## Features

### Core Capabilities
- **Multiple Time Horizons**: 1Y, 3Y, 5Y, 10Y, YTD, or custom date ranges
- **Benchmark Comparison**: Compare against SPY, QQQ, IWM, VEA, AGG
- **Flexible Rebalancing**: Daily, weekly, monthly, or quarterly rebalancing
- **Transaction Costs**: Model trading costs during rebalancing
- **Performance Metrics**: Complete risk and return analytics

### Performance Metrics

#### Returns
- **Total Return**: Cumulative gain/loss as percentage
- **Annualized Return (CAGR)**: Compound Annual Growth Rate
- **Alpha**: Excess return vs benchmark (in percentage points)

#### Risk Metrics
- **Volatility (Annual)**: Standard deviation of daily returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return (>1 is good)
- **Sortino Ratio**: Return per unit of downside risk

#### Win/Loss Statistics
- **Win Rate**: Percentage of periods with positive returns
- **Winning/Losing Periods**: Count of each
- **Best/Worst Period**: Largest single-period gains/losses
- **Best/Worst Month**: Dates of extreme performance

## Backend Implementation

### File Structure

```
backend/
├── backtest_service.py          # Core backtesting engine
├── backtest_routes.py           # FastAPI endpoints
└── tests/
    ├── test_backtest_service.py # Service unit tests
    └── test_backtest_routes.py  # Route tests
```

### BacktestService Class

**Location**: `/backend/backtest_service.py`

Main backtesting engine with the following key methods:

#### `run_backtest(config: BacktestConfig) -> BacktestResult`

Executes a complete backtest with the given configuration.

**Parameters**:
- `config`: BacktestConfig with strategy parameters

**Returns**:
- `BacktestResult`: Complete performance metrics and time series data

**Example**:
```python
from backtest_service import BacktestService, BacktestConfig
from datetime import date, timedelta

service = BacktestService()

config = BacktestConfig(
    strategy_id="my_strategy",
    initial_capital=10000,
    start_date=date(2020, 1, 1),
    end_date=date(2025, 1, 1),
    rebalance_frequency="monthly",
    benchmark="SPY",
    compositions=[
        {"AAPL": 0.5, "MSFT": 0.5}
    ]
)

result = service.run_backtest(config)
print(f"Total Return: {result.total_return_pct:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

#### Key Data Structures

**BacktestConfig**
```python
@dataclass
class BacktestConfig:
    strategy_id: str
    initial_capital: float
    start_date: date
    end_date: date
    rebalance_frequency: str = "monthly"
    transaction_cost_pct: float = 0.001
    benchmark: str = "SPY"
    compositions: List[Dict[str, float]] = []
```

**BacktestResult**
```python
@dataclass
class BacktestResult:
    # Performance metrics
    total_return_pct: float
    annualized_return_pct: float
    alpha: float

    # Risk metrics
    volatility_annual_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float

    # Time series data
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]

    # ... and more
```

### API Routes

**Base URL**: `/api/backtest`

#### `POST /run` - Execute Backtest

Run a backtest on a portfolio composition.

**Request**:
```json
{
  "strategy_id": "my_strategy",
  "initial_capital": 10000,
  "start_date": "2020-01-01",
  "end_date": "2025-01-01",
  "rebalance_frequency": "monthly",
  "benchmark": "SPY",
  "compositions": [
    {
      "AAPL": 0.5,
      "MSFT": 0.5
    }
  ]
}
```

**Response**:
```json
{
  "total_return_pct": 125.50,
  "annualized_return_pct": 18.5,
  "benchmark_return_pct": 95.30,
  "alpha": 2.3,
  "volatility_annual_pct": 18.2,
  "max_drawdown_pct": -28.5,
  "sharpe_ratio": 1.02,
  "sortino_ratio": 1.45,
  "winning_periods": 890,
  "losing_periods": 252,
  "win_rate_pct": 77.9,
  "equity_curve": [...],
  "drawdown_curve": [...],
  "monthly_returns": [...]
}
```

#### `GET /presets` - Get Time Period Presets

Get available backtest time period configurations.

**Response**:
```json
[
  {
    "id": "1y",
    "label": "1 Year",
    "description": "Last 12 months",
    "start_offset_years": 1
  },
  {
    "id": "5y",
    "label": "5 Years",
    "description": "Last 5 years",
    "start_offset_years": 5
  }
]
```

#### `GET /benchmarks` - Get Available Benchmarks

List available benchmark indices for comparison.

**Response**:
```json
[
  {
    "id": "SPY",
    "name": "S&P 500",
    "description": "500 largest US companies",
    "asset_class": "US Equities"
  },
  {
    "id": "QQQ",
    "name": "Nasdaq 100",
    "description": "Top 100 non-financial US companies",
    "asset_class": "US Tech Equities"
  }
]
```

#### `GET /rebalance-frequencies` - Get Rebalance Options

Get available rebalancing frequency options.

**Response**:
```json
[
  {
    "id": "daily",
    "label": "Daily",
    "description": "Rebalance every trading day"
  },
  {
    "id": "monthly",
    "label": "Monthly",
    "description": "Rebalance at month-end"
  }
]
```

#### `GET /stats` - Get Backtest Statistics Info

Get general backtest statistics and system configuration.

**Response**:
```json
{
  "default_initial_capital": 10000,
  "min_initial_capital": 100,
  "max_initial_capital": 10000000,
  "risk_free_rate_annual": 0.02,
  "default_rebalance_frequency": "monthly",
  "available_benchmarks": ["SPY", "QQQ", "IWM", "VEA", "AGG"]
}
```

## Frontend Implementation

### File Structure

```
frontend/
├── types/
│   └── backtest.ts              # TypeScript type definitions
├── hooks/
│   └── useBacktest.ts           # React hook for backtest state
└── components/
    └── backtest/
        ├── BacktestPanel.tsx    # Main config panel
        ├── BacktestMetrics.tsx  # Metrics display cards
        ├── EquityCurveChart.tsx # Performance chart
        └── index.ts             # Exports
```

### useBacktest Hook

**Location**: `/frontend/hooks/useBacktest.ts`

React hook for managing backtest state and API interactions.

**Usage**:
```typescript
import { useBacktest } from '@/hooks/useBacktest';

function MyComponent() {
  const {
    isLoading,
    error,
    result,
    presets,
    benchmarks,
    runBacktest,
    loadMetadata,
  } = useBacktest();

  useEffect(() => {
    loadMetadata(); // Load presets, benchmarks, etc.
  }, [loadMetadata]);

  const handleTest = async () => {
    const config = {
      strategy_id: 'my_strategy',
      initial_capital: 10000,
      rebalance_frequency: 'monthly',
      benchmark: 'SPY',
      compositions: [{ AAPL: 0.5, MSFT: 0.5 }],
    };

    const result = await runBacktest(config);
    if (result) {
      console.log(`Return: ${result.total_return_pct.toFixed(2)}%`);
    }
  };

  return (
    <div>
      <button onClick={handleTest} disabled={isLoading}>
        Run Backtest
      </button>
      {error && <p className="error">{error}</p>}
      {result && <BacktestMetrics result={result} />}
    </div>
  );
}
```

### BacktestPanel Component

**Location**: `/frontend/components/backtest/BacktestPanel.tsx`

Complete UI panel for configuring and running backtests.

**Features**:
- Quick preset buttons (1Y, 3Y, 5Y, 10Y, YTD)
- Initial capital input
- Benchmark selector
- Rebalance frequency selector
- Custom date range picker
- Portfolio allocation display
- Run/clear buttons

**Props**:
```typescript
interface BacktestPanelProps {
  strategyId: string;
  compositions: CompositionItem[];
  onClose?: () => void;
}
```

**Usage**:
```typescript
import { BacktestPanel } from '@/components/backtest';

export function StrategyPage() {
  return (
    <BacktestPanel
      strategyId="strategy_123"
      compositions={[
        { ticker: 'AAPL', weight: 0.5 },
        { ticker: 'MSFT', weight: 0.5 },
      ]}
      onClose={() => console.log('Closed')}
    />
  );
}
```

### BacktestMetrics Component

**Location**: `/frontend/components/backtest/BacktestMetrics.tsx`

Display key performance metrics in card format.

**Features**:
- Color-coded metrics (green for positive, red for negative)
- Tooltips with explanations
- Benchmark comparison
- Win rate statistics
- Final portfolio values
- Summary information

### EquityCurveChart Component

**Location**: `/frontend/components/backtest/EquityCurveChart.tsx`

Interactive chart showing portfolio vs benchmark performance over time.

**Features**:
- Line chart of portfolio and benchmark values
- Area chart of drawdown from peak
- Responsive layout
- Custom tooltips
- Downsampled data for performance

## Configuration

### Environment Variables

Add to `/backend/.env`:
```
# Backtest Service Configuration
BACKTEST_RISK_FREE_RATE=0.02
BACKTEST_DEFAULT_INITIAL_CAPITAL=10000
BACKTEST_MIN_INITIAL_CAPITAL=100
BACKTEST_MAX_INITIAL_CAPITAL=10000000
BACKTEST_DEFAULT_BENCHMARK=SPY
BACKTEST_DEFAULT_REBALANCE=monthly
BACKTEST_DEFAULT_TRANSACTION_COST=0.001
```

## Testing

### Running Tests

```bash
# Run all backtest tests
pytest backend/tests/test_backtest_*.py -v

# Run specific test file
pytest backend/tests/test_backtest_service.py -v

# Run with coverage
pytest backend/tests/test_backtest_*.py --cov=backtest_service --cov=backtest_routes
```

### Test Coverage

- **BacktestService**: 90%+ coverage
  - Backtest execution
  - Metric calculations
  - Data handling
  - Edge cases

- **BacktestRoutes**: 85%+ coverage
  - Request validation
  - Route handlers
  - Error handling
  - Response formats

## Performance Considerations

### Optimizations

1. **Data Downsampling**: Equity curves are downsampled to ~250 points for frontend performance
2. **Lazy Loading**: Price data is loaded on-demand from Parquet store
3. **Caching**: Consider caching common backtest periods
4. **Dummy Data**: Falls back to dummy data if historical data unavailable

### Limitations

- Current implementation uses dummy price data when Parquet store unavailable
- Maximum backtest period: 30 years (by design)
- Minimum data points: 2 days
- Rebalancing assumes perfect execution at daily open prices

## Metrics Explanation

### Sharpe Ratio
Measures risk-adjusted return. Formula:
```
Sharpe = (Annual Return - Risk-Free Rate) / Annual Volatility
```
- `> 1.0`: Good risk-adjusted returns
- `> 2.0`: Excellent
- `< 0`: Returns below risk-free rate

### Sortino Ratio
Similar to Sharpe but only considers downside volatility:
```
Sortino = (Annual Return - Risk-Free Rate) / Downside Volatility
```
- Generally higher than Sharpe for same portfolio
- Better for strategies with asymmetric returns

### Alpha
Excess return compared to benchmark:
```
Alpha = Portfolio Return - Benchmark Return
```
- Positive: Outperformance
- Negative: Underperformance

### Maximum Drawdown
Largest peak-to-trough decline in portfolio value:
```
Max Drawdown = (Peak Value - Trough Value) / Peak Value
```
- Always non-positive
- More negative = worse drawdown
- Important for risk assessment

## Troubleshooting

### Common Issues

**1. "No data available" error**
- Ensure Parquet store has price data
- Check data date ranges
- System falls back to dummy data

**2. Weights don't sum to 1.0**
- Verify composition weights sum to exactly 1.0
- Allowed tolerance: ±0.01
- Example: [0.6, 0.4] ✓ | [0.5, 0.5] ✓ | [0.7, 0.2] ✗

**3. Sharpe/Sortino ratios are unrealistic**
- Verify volatility is non-zero
- Check if returns are truly random
- Consider risk-free rate assumption (2%)

**4. Backtest takes too long**
- Reduce daily rebalancing frequency to monthly
- Shorten test period
- Check system resources

## Future Enhancements

1. **Advanced Features**:
   - Dividend and interest modeling
   - Tax optimization (tax-loss harvesting simulation)
   - Slippage and market impact modeling
   - Multiple currency support

2. **Data**:
   - Real historical prices from live data sources
   - Caching of computed backtests
   - Historical dividend data

3. **Analytics**:
   - Correlation matrix over time
   - Risk decomposition
   - Attribution analysis
   - Monte Carlo simulations

4. **UI**:
   - Compare multiple strategies
   - Sensitivity analysis (parameter sweeps)
   - Rolling windows analysis
   - Tear sheets generation

## API Integration Example

```typescript
// Full example: Run and display backtest
async function runFullBacktest() {
  const compositions: CompositionItem[] = [
    { ticker: 'AAPL', weight: 0.3 },
    { ticker: 'MSFT', weight: 0.3 },
    { ticker: 'GOOGL', weight: 0.4 },
  ];

  const request: BacktestRequest = {
    strategy_id: 'diversified_tech',
    initial_capital: 50000,
    start_date: '2020-01-01',
    end_date: '2025-01-01',
    rebalance_frequency: 'quarterly',
    benchmark: 'QQQ',
    compositions: compositions.map((c) => ({
      [c.ticker]: c.weight,
    })),
  };

  const response = await fetch('/api/backtest/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  const result: BacktestResult = await response.json();

  console.log('Backtest Results:');
  console.log(`Total Return: ${result.total_return_pct.toFixed(2)}%`);
  console.log(`Annual Return: ${result.annualized_return_pct.toFixed(2)}%`);
  console.log(`Sharpe Ratio: ${result.sharpe_ratio.toFixed(2)}`);
  console.log(`Max Drawdown: ${result.max_drawdown_pct.toFixed(2)}%`);
  console.log(`vs ${result.benchmark}: ${result.alpha > 0 ? '+' : ''}${result.alpha.toFixed(2)}%`);

  return result;
}
```

## References

- Sharpe Ratio: https://en.wikipedia.org/wiki/Sharpe_ratio
- Sortino Ratio: https://en.wikipedia.org/wiki/Sortino_ratio
- Maximum Drawdown: https://en.wikipedia.org/wiki/Drawdown_(economics)
- CAGR: https://en.wikipedia.org/wiki/Compound_annual_growth_rate
