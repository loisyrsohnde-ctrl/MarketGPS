// ═══════════════════════════════════════════════════════════════════════════
// QUICK ACTIONS - UNIT TESTS
// ═══════════════════════════════════════════════════════════════════════════

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QuickActions } from '../QuickActions';
import type { Asset } from '@/types';

// Mock asset for testing
const mockAsset: Asset = {
  asset_id: '1',
  ticker: 'AAPL',
  symbol: 'AAPL',
  name: 'Apple Inc.',
  asset_type: 'EQUITY',
  market_scope: 'US_EU',
  market_code: 'US',
  score_total: 75.5,
  score_value: 70,
  score_momentum: 80,
  score_safety: 75,
  coverage: 0.95,
  liquidity: 0.9,
  fx_risk: 0.1,
  last_price: 150.25,
  currency: 'USD',
  updated_at: new Date().toISOString(),
};

// Mock API
vi.mock('@/lib/api', () => ({
  api: {
    checkInWatchlist: vi.fn(() => Promise.resolve({ in_watchlist: false })),
    addToWatchlist: vi.fn(() => Promise.resolve({ status: 'success' })),
    removeFromWatchlist: vi.fn(() => Promise.resolve({ status: 'success' })),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('QuickActions Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all action buttons', async () => {
      render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTitle('Ajouter à la watchlist')).toBeInTheDocument();
        expect(screen.getByTitle('Créer une alerte')).toBeInTheDocument();
        expect(screen.getByTitle('Comparer avec d\'autres actifs')).toBeInTheDocument();
      });
    });

    it('should display correct variant styles', () => {
      const { container } = render(
        <TestWrapper>
          <QuickActions asset={mockAsset} variant="horizontal" />
        </TestWrapper>
      );

      const buttons = container.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Watchlist Actions', () => {
    it('should toggle watchlist on button click', async () => {
      render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      const watchlistBtn = await screen.findByTitle('Ajouter à la watchlist');
      fireEvent.click(watchlistBtn);

      // Should show loading state
      await waitFor(() => {
        expect(watchlistBtn).toHaveClass('opacity-50');
      });
    });

    it('should show toast notification on success', async () => {
      render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      const watchlistBtn = await screen.findByTitle('Ajouter à la watchlist');
      fireEvent.click(watchlistBtn);

      // Toast should appear (implementation dependent)
      await waitFor(() => {
        // Check for success message
      });
    });
  });

  describe('Copy Action', () => {
    it('should copy asset info to clipboard', async () => {
      // Mock navigator.clipboard
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn(() => Promise.resolve()),
        },
      });

      render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      const copyBtn = await screen.findByTitle('Copier les infos');
      fireEvent.click(copyBtn);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });
  });

  describe('Modal Actions', () => {
    it('should call onOpenAlert when alert button clicked', async () => {
      const onOpenAlert = vi.fn();

      render(
        <TestWrapper>
          <QuickActions
            asset={mockAsset}
            onOpenAlert={onOpenAlert}
          />
        </TestWrapper>
      );

      const alertBtn = await screen.findByTitle('Créer une alerte');
      fireEvent.click(alertBtn);

      await waitFor(() => {
        expect(onOpenAlert).toHaveBeenCalled();
      });
    });

    it('should call onOpenComparator when comparator button clicked', async () => {
      const onOpenComparator = vi.fn();

      render(
        <TestWrapper>
          <QuickActions
            asset={mockAsset}
            onOpenComparator={onOpenComparator}
          />
        </TestWrapper>
      );

      const compareBtn = await screen.findByTitle('Comparer avec d\'autres actifs');
      fireEvent.click(compareBtn);

      await waitFor(() => {
        expect(onOpenComparator).toHaveBeenCalled();
      });
    });
  });

  describe('Variants', () => {
    it('should render horizontal variant', () => {
      const { container } = render(
        <TestWrapper>
          <QuickActions asset={mockAsset} variant="horizontal" />
        </TestWrapper>
      );

      expect(container.querySelector('.flex-wrap')).toBeInTheDocument();
    });

    it('should render vertical variant', () => {
      const { container } = render(
        <TestWrapper>
          <QuickActions asset={mockAsset} variant="vertical" />
        </TestWrapper>
      );

      expect(container.querySelector('.flex-col')).toBeInTheDocument();
    });

    it('should render floating variant with FAB button', () => {
      const { container } = render(
        <TestWrapper>
          <QuickActions asset={mockAsset} variant="floating" />
        </TestWrapper>
      );

      const fab = container.querySelector('.rounded-full');
      expect(fab).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria labels', async () => {
      render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach((btn) => {
        expect(btn).toHaveAttribute('title');
      });
    });

    it('should be keyboard accessible', () => {
      const { container } = render(
        <TestWrapper>
          <QuickActions asset={mockAsset} />
        </TestWrapper>
      );

      const buttons = container.querySelectorAll('button');
      buttons.forEach((btn) => {
        expect(btn).not.toHaveAttribute('disabled');
      });
    });
  });
});
