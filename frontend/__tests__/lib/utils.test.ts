import {
  cn,
  formatNumber,
  formatNumberSafe,
  formatScore,
  isAssetScored,
  formatPercent,
  formatCurrency,
  formatDate,
  formatRelativeTime,
  truncate,
  getInitials,
  debounce,
  sleep,
  isClient,
  isServer,
  safeJsonParse,
  generateId,
  clamp,
  getLiquidityLabel,
  getRiskLabel,
  SCORE_FALLBACK_TEXT,
  UNSCORED_LABEL,
} from '@/lib/utils';

describe('Utils - Constants', () => {
  it('has correct SCORE_FALLBACK_TEXT', () => {
    expect(SCORE_FALLBACK_TEXT).toBe('—');
  });

  it('has correct UNSCORED_LABEL', () => {
    expect(UNSCORED_LABEL).toBe('Non scoré');
  });
});

describe('Utils - cn (Tailwind classnames)', () => {
  it('merges tailwind classes correctly', () => {
    const result = cn('px-2', 'px-4');
    expect(result).toContain('px-4');
  });

  it('handles conditional classes', () => {
    const result = cn('px-2', true && 'py-2', false && 'py-4');
    expect(result).toContain('px-2');
    expect(result).toContain('py-2');
    expect(result).not.toContain('py-4');
  });

  it('handles empty input', () => {
    expect(cn()).toBe('');
  });
});

describe('Utils - formatNumber', () => {
  it('formats number with French locale', () => {
    const result = formatNumber(1234567);
    expect(result).toMatch(/1.*234.*567/);
  });

  it('handles decimal numbers', () => {
    const result = formatNumber(1234.56);
    expect(result).toBeTruthy();
  });

  it('handles zero', () => {
    expect(formatNumber(0)).toBe('0');
  });

  it('handles negative numbers', () => {
    const result = formatNumber(-1234);
    expect(result).toContain('1234');
  });
});

describe('Utils - formatNumberSafe', () => {
  it('formats number safely', () => {
    const result = formatNumberSafe(1000);
    expect(result).toContain('1');
  });

  it('returns fallback text for null', () => {
    expect(formatNumberSafe(null)).toBe(SCORE_FALLBACK_TEXT);
  });

  it('returns fallback text for undefined', () => {
    expect(formatNumberSafe(undefined)).toBe(SCORE_FALLBACK_TEXT);
  });

  it('uses space as thousands separator', () => {
    const result = formatNumberSafe(1000000);
    expect(result).toBe('1 000 000');
  });
});

describe('Utils - formatScore', () => {
  it('formats score as integer by default', () => {
    expect(formatScore(85.7)).toBe('86');
  });

  it('formats score with decimals', () => {
    const result = formatScore(85.7, { decimals: 1 });
    expect(result).toBe('85.7');
  });

  it('includes unit when requested', () => {
    const result = formatScore(85, { showUnit: true });
    expect(result).toBe('85/100');
  });

  it('returns fallback text for null score', () => {
    expect(formatScore(null)).toBe(SCORE_FALLBACK_TEXT);
  });

  it('returns fallback text for undefined score', () => {
    expect(formatScore(undefined)).toBe(SCORE_FALLBACK_TEXT);
  });

  it('uses custom fallback text', () => {
    const result = formatScore(null, { fallback: 'N/A' });
    expect(result).toBe('N/A');
  });

  it('handles zero score', () => {
    expect(formatScore(0)).toBe('0');
  });
});

describe('Utils - isAssetScored', () => {
  it('returns true for scored asset', () => {
    expect(isAssetScored({ score_total: 75 })).toBe(true);
  });

  it('returns true for zero score', () => {
    expect(isAssetScored({ score_total: 0 })).toBe(true);
  });

  it('returns false for null score', () => {
    expect(isAssetScored({ score_total: null })).toBe(false);
  });

  it('returns false for undefined score', () => {
    expect(isAssetScored({ score_total: undefined })).toBe(false);
  });

  it('returns false for null asset', () => {
    expect(isAssetScored(null)).toBe(false);
  });

  it('returns false for undefined asset', () => {
    expect(isAssetScored(undefined)).toBe(false);
  });
});

describe('Utils - formatPercent', () => {
  it('formats percentage', () => {
    expect(formatPercent(50)).toBe('50%');
  });

  it('formats percentage with decimals', () => {
    expect(formatPercent(50.5, 1)).toBe('50.5%');
  });

  it('returns fallback for null', () => {
    expect(formatPercent(null)).toBe('—');
  });

  it('formats zero percent', () => {
    expect(formatPercent(0)).toBe('0%');
  });
});

describe('Utils - formatCurrency', () => {
  it('formats currency in EUR by default', () => {
    const result = formatCurrency(1000);
    expect(result).toContain('1');
    expect(result).toContain('000');
  });

  it('formats currency with different currency code', () => {
    const result = formatCurrency(1000, 'USD');
    expect(result).toBeTruthy();
  });

  it('handles decimal values', () => {
    const result = formatCurrency(1000.50);
    expect(result).toBeTruthy();
  });

  it('handles zero amount', () => {
    const result = formatCurrency(0);
    expect(result).toBeTruthy();
  });
});

describe('Utils - formatDate', () => {
  it('formats date in short format', () => {
    const date = new Date('2024-02-08');
    const result = formatDate(date, 'short');
    expect(result).toMatch(/08\/02\/2024|02\/08\/2024/);
  });

  it('formats date in long format', () => {
    const date = new Date('2024-02-08');
    const result = formatDate(date, 'long');
    expect(result).toBeTruthy();
  });

  it('accepts string date', () => {
    const result = formatDate('2024-02-08', 'short');
    expect(result).not.toBe('—');
  });

  it('returns fallback for null date', () => {
    expect(formatDate(null)).toBe('—');
  });

  it('returns fallback for undefined date', () => {
    expect(formatDate(undefined)).toBe('—');
  });

  it('returns fallback for invalid date', () => {
    expect(formatDate('invalid-date')).toBe('—');
  });

  it('defaults to short format', () => {
    const date = new Date('2024-02-08');
    const result = formatDate(date);
    expect(result).toMatch(/08\/02\/2024|02\/08\/2024/);
  });
});

describe('Utils - formatRelativeTime', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-02-08T12:00:00Z'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows relative time for recent past', () => {
    const date = new Date('2024-02-08T11:50:00Z');
    const result = formatRelativeTime(date);
    expect(result).toBe('il y a 10min');
  });

  it('shows days for old dates', () => {
    const date = new Date('2024-02-06T12:00:00Z');
    const result = formatRelativeTime(date);
    expect(result).toBe('il y a 2j');
  });

  it('returns fallback for null', () => {
    expect(formatRelativeTime(null)).toBe('—');
  });

  it('returns fallback for undefined', () => {
    expect(formatRelativeTime(undefined)).toBe('—');
  });

  it('returns instant for very recent times', () => {
    const date = new Date('2024-02-08T11:59:50Z');
    const result = formatRelativeTime(date);
    expect(result).toBe('à l\'instant');
  });
});

describe('Utils - truncate', () => {
  it('truncates long text', () => {
    const result = truncate('Hello World', 5);
    expect(result).toBe('Hello...');
  });

  it('does not truncate short text', () => {
    const result = truncate('Hi', 5);
    expect(result).toBe('Hi');
  });

  it('truncates exactly at maxLength', () => {
    const result = truncate('12345678', 5);
    expect(result).toHaveLength(8); // 5 chars + '...'
  });

  it('handles empty string', () => {
    expect(truncate('', 5)).toBe('');
  });
});

describe('Utils - getInitials', () => {
  it('extracts initials from name', () => {
    expect(getInitials('John Doe')).toBe('JD');
  });

  it('handles single name', () => {
    expect(getInitials('John')).toBe('J');
  });

  it('handles multiple parts', () => {
    expect(getInitials('John Michael Doe')).toBe('JM');
  });

  it('converts to uppercase', () => {
    expect(getInitials('john doe')).toBe('JD');
  });

  it('limits to 2 characters', () => {
    expect(getInitials('A B C D')).toBe('AB');
  });
});

describe('Utils - debounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('delays function execution', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 500);

    debounced();
    expect(fn).not.toHaveBeenCalled();

    jest.advanceTimersByTime(500);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('cancels previous calls', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 500);

    debounced();
    jest.advanceTimersByTime(200);
    debounced();
    jest.advanceTimersByTime(500);

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('passes arguments to function', () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 500);

    debounced(1, 2, 3);
    jest.advanceTimersByTime(500);

    expect(fn).toHaveBeenCalledWith(1, 2, 3);
  });
});

describe('Utils - sleep', () => {
  it('resolves after delay', async () => {
    const start = Date.now();
    await sleep(100);
    const elapsed = Date.now() - start;

    expect(elapsed).toBeGreaterThanOrEqual(100);
  });

  it('returns a promise', () => {
    const result = sleep(10);
    expect(result instanceof Promise).toBe(true);
  });
});

describe('Utils - isClient and isServer', () => {
  it('isClient returns true in browser', () => {
    expect(isClient).toBe(true);
  });

  it('isServer returns false in browser', () => {
    expect(isServer).toBe(false);
  });
});

describe('Utils - safeJsonParse', () => {
  it('parses valid JSON', () => {
    const result = safeJsonParse('{"key": "value"}', null);
    expect(result).toEqual({ key: 'value' });
  });

  it('returns fallback for invalid JSON', () => {
    const fallback = { default: true };
    const result = safeJsonParse('invalid json', fallback);
    expect(result).toEqual(fallback);
  });

  it('returns fallback for empty string', () => {
    const fallback = {};
    const result = safeJsonParse('', fallback);
    expect(result).toEqual(fallback);
  });
});

describe('Utils - generateId', () => {
  it('generates unique IDs', () => {
    const id1 = generateId();
    const id2 = generateId();
    expect(id1).not.toBe(id2);
  });

  it('generates alphanumeric IDs', () => {
    const id = generateId();
    expect(/^[a-z0-9]+$/.test(id)).toBe(true);
  });

  it('generates IDs of correct length', () => {
    const id = generateId();
    expect(id.length).toBe(7);
  });
});

describe('Utils - clamp', () => {
  it('clamps value within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('clamps to minimum', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it('clamps to maximum', () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });

  it('handles negative range', () => {
    expect(clamp(-5, -10, -1)).toBe(-5);
  });
});

describe('Utils - getLiquidityLabel', () => {
  it('returns "Élevée" for high liquidity', () => {
    expect(getLiquidityLabel(0.8)).toBe('Élevée');
  });

  it('returns "Moyenne" for medium liquidity', () => {
    expect(getLiquidityLabel(0.5)).toBe('Moyenne');
  });

  it('returns "Faible" for low liquidity', () => {
    expect(getLiquidityLabel(0.2)).toBe('Faible');
  });

  it('returns "N/A" for null liquidity', () => {
    expect(getLiquidityLabel(null)).toBe('N/A');
  });

  it('handles boundary value 0.7', () => {
    expect(getLiquidityLabel(0.7)).toBe('Élevée');
  });

  it('handles boundary value 0.4', () => {
    expect(getLiquidityLabel(0.4)).toBe('Moyenne');
  });
});

describe('Utils - getRiskLabel', () => {
  it('returns "Faible" for low risk', () => {
    expect(getRiskLabel(0.2)).toBe('Faible');
  });

  it('returns "Modéré" for medium risk', () => {
    expect(getRiskLabel(0.5)).toBe('Modéré');
  });

  it('returns "Élevé" for high risk', () => {
    expect(getRiskLabel(0.8)).toBe('Élevé');
  });

  it('returns "N/A" for null risk', () => {
    expect(getRiskLabel(null)).toBe('N/A');
  });

  it('handles boundary value 0.3', () => {
    expect(getRiskLabel(0.3)).toBe('Faible');
  });

  it('handles boundary value 0.6', () => {
    expect(getRiskLabel(0.6)).toBe('Modéré');
  });
});
