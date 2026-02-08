import {
  getTopScored,
  searchAssets,
  getAssetDetails,
  getAssetChart,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  checkInWatchlist,
  getScopeCounts,
  getAssetTypeCounts,
  getLandingMetrics,
  getCountsV2,
  createCheckoutSession,
  getSubscription,
  getMySubscription,
  createPortalSession,
  calculateScoreOnDemand,
  getUserQuota,
  getUniverseMetrics,
} from '@/lib/api';

// Mock config
jest.mock('@/lib/config', () => ({
  getApiBaseUrl: () => 'https://api.example.com',
}));

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('getTopScored', () => {
    it('builds correct URL without params', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [], total: 0 }),
      });

      await getTopScored();

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/assets/top-scored',
        expect.any(Object)
      );
    });

    it('builds correct URL with params', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [], total: 0 }),
      });

      await getTopScored({
        limit: 20,
        offset: 0,
        market_scope: 'US_EU',
        asset_type: 'STOCKS',
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=20'),
        expect.any(Object)
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('market_scope=US_EU'),
        expect.any(Object)
      );
    });

    it('includes auth token when provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const token = 'test-token';
      await getTopScored({}, token);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${token}`,
          }),
        })
      );
    });

    it('handles API response correctly', async () => {
      const mockData = { data: [{ ticker: 'AAPL', score_total: 85 }], total: 1 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await getTopScored();

      expect(result).toEqual(mockData);
    });

    it('handles API errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Not found' }),
      });

      await expect(getTopScored()).rejects.toThrow('Not found');
    });

    it('handles network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(getTopScored()).rejects.toThrow('Network error');
    });
  });

  describe('searchAssets', () => {
    it('sends correct query parameter', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      await searchAssets({ q: 'apple' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('q=apple'),
        expect.any(Object)
      );
    });

    it('includes all parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      await searchAssets({
        q: 'apple',
        market_scope: 'US_EU',
        limit: 10,
      });

      const callUrl = (global.fetch as jest.Mock).mock.calls[0][0];
      expect(callUrl).toContain('q=apple');
      expect(callUrl).toContain('market_scope=US_EU');
      expect(callUrl).toContain('limit=10');
    });

    it('returns assets array', async () => {
      const mockAssets = [{ ticker: 'AAPL' }, { ticker: 'GOOGL' }];
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAssets,
      });

      const result = await searchAssets({ q: 'test' });

      expect(result).toEqual(mockAssets);
    });

    it('includes auth token when provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      await searchAssets({ q: 'test' }, 'auth-token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer auth-token',
          }),
        })
      );
    });

    it('handles empty search results', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      const result = await searchAssets({ q: 'xyz' });

      expect(result).toEqual([]);
    });
  });

  describe('getAssetDetails', () => {
    it('builds correct endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await getAssetDetails('AAPL');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assets/AAPL'),
        expect.any(Object)
      );
    });

    it('includes auth token', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await getAssetDetails('AAPL', 'token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer token',
          }),
        })
      );
    });
  });

  describe('getAssetChart', () => {
    it('builds correct URL with period', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      await getAssetChart('AAPL', '30d');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assets/AAPL/chart?period=30d'),
        expect.any(Object)
      );
    });

    it('defaults to 30d period', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      await getAssetChart('AAPL');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('period=30d'),
        expect.any(Object)
      );
    });
  });

  describe('Watchlist API', () => {
    it('getWatchlist returns items array', async () => {
      const mockWatchlist = [{ ticker: 'AAPL' }, { ticker: 'GOOGL' }];
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlist,
      });

      const result = await getWatchlist('user-123');

      expect(result).toEqual(mockWatchlist);
    });

    it('addToWatchlist sends correct data', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'added' }),
      });

      await addToWatchlist('AAPL', 'user-123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('AAPL'),
        })
      );
    });

    it('removeFromWatchlist sends DELETE request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'removed' }),
      });

      await removeFromWatchlist('AAPL', 'user-123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('checkInWatchlist returns boolean', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ in_watchlist: true }),
      });

      const result = await checkInWatchlist('AAPL');

      expect(result).toEqual({ in_watchlist: true });
    });
  });

  describe('Metrics API', () => {
    it('getScopeCounts returns counts', async () => {
      const mockCounts = { US_EU: 100, AFRICA: 50 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCounts,
      });

      const result = await getScopeCounts();

      expect(result).toEqual(mockCounts);
    });

    it('getAssetTypeCounts handles scope filter', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ STOCKS: { count: 100 } }),
      });

      await getAssetTypeCounts('US_EU');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('market_scope=US_EU'),
        expect.any(Object)
      );
    });

    it('getLandingMetrics returns metrics', async () => {
      const mockMetrics = { total: 1000, scored: 500 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetrics,
      });

      const result = await getLandingMetrics();

      expect(result).toEqual(mockMetrics);
    });

    it('getCountsV2 includes all filter parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total: 100 }),
      });

      await getCountsV2({
        market_scope: 'US_EU',
        asset_type: 'STOCKS',
        country: 'FR',
        only_scored: true,
      });

      const callUrl = (global.fetch as jest.Mock).mock.calls[0][0];
      expect(callUrl).toContain('market_scope=US_EU');
      expect(callUrl).toContain('asset_type=STOCKS');
      expect(callUrl).toContain('country=FR');
      expect(callUrl).toContain('only_scored=true');
    });
  });

  describe('Billing API', () => {
    beforeEach(() => {
      global.window = {
        location: {
          origin: 'https://marketgps.com',
        },
      } as any;
    });

    it('createCheckoutSession includes URLs', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ checkout_url: 'https://stripe.com/pay' }),
      });

      await createCheckoutSession('monthly', 'token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('success_url'),
        })
      );
    });

    it('getSubscription includes auth token', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ plan: 'monthly' }),
      });

      await getSubscription('token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer token',
          }),
        })
      );
    });

    it('getMySubscription returns subscription status', async () => {
      const mockStatus = { plan: 'monthly', is_active: true };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus,
      });

      const result = await getMySubscription('token');

      expect(result).toEqual(mockStatus);
    });

    it('createPortalSession sends POST request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ url: 'https://portal.stripe.com' }),
      });

      await createPortalSession('token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer token',
          }),
        })
      );
    });
  });

  describe('On-Demand Scoring API', () => {
    it('calculateScoreOnDemand sends POST request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ score_total: 75 }),
      });

      await calculateScoreOnDemand('AAPL');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/assets/AAPL/score'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('calculateScoreOnDemand includes force parameter', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ score_total: 75 }),
      });

      await calculateScoreOnDemand('AAPL', true);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('force=true'),
        expect.any(Object)
      );
    });

    it('calculateScoreOnDemand includes auth token', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ score_total: 75 }),
      });

      await calculateScoreOnDemand('AAPL', false, 'token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer token',
          }),
        })
      );
    });

    it('getUserQuota returns quota status', async () => {
      const mockQuota = { remaining: 10, daily_limit: 100 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockQuota,
      });

      const result = await getUserQuota('token');

      expect(result).toEqual(mockQuota);
    });

    it('getUniverseMetrics returns metrics', async () => {
      const mockMetrics = { total_assets: 5000 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetrics,
      });

      const result = await getUniverseMetrics();

      expect(result).toEqual(mockMetrics);
    });
  });

  describe('Error Handling', () => {
    it('handles 4xx errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Bad request' }),
      });

      await expect(getTopScored()).rejects.toThrow('Bad request');
    });

    it('handles 5xx errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Server error' }),
      });

      await expect(getTopScored()).rejects.toThrow('Server error');
    });

    it('handles JSON parse errors in error response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(getTopScored()).rejects.toThrow('API Error: 500');
    });

    it('sets Content-Type header', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await getTopScored();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });
});
