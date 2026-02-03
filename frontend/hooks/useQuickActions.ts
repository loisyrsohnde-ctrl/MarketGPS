'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Asset } from '@/types';

// ═══════════════════════════════════════════════════════════════════════════
// QUICK ACTIONS HOOK
// ═══════════════════════════════════════════════════════════════════════════

interface UseQuickActionsProps {
  assetId: string;
  ticker: string;
  userId?: string;
  marketScope?: string;
  onActionComplete?: (action: string, success: boolean) => void;
}

interface QuickActionResult {
  success: boolean;
  message: string;
  data?: any;
}

export function useQuickActions({
  assetId,
  ticker,
  userId = 'default',
  marketScope = 'US_EU',
  onActionComplete,
}: UseQuickActionsProps) {
  const queryClient = useQueryClient();
  const [lastAction, setLastAction] = useState<string | null>(null);

  // Check if asset is in watchlist
  const { data: isInWatchlist = false, refetch: refetchWatchlist } = useQuery({
    queryKey: ['watchlist-check', ticker, userId],
    queryFn: async () => {
      try {
        const result = await api.checkInWatchlist(ticker, userId);
        return result.in_watchlist;
      } catch {
        return false;
      }
    },
  });

  // Watchlist toggle mutation
  const watchlistMutation = useMutation({
    mutationFn: async (add: boolean): Promise<QuickActionResult> => {
      try {
        if (add) {
          await api.addToWatchlist(ticker, userId, marketScope);
          return { success: true, message: 'Ajouté à la watchlist' };
        } else {
          await api.removeFromWatchlist(ticker, userId);
          return { success: true, message: 'Retiré de la watchlist' };
        }
      } catch (error) {
        return {
          success: false,
          message: error instanceof Error ? error.message : 'Erreur lors de l\'opération',
        };
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['watchlist-check', ticker, userId] });
      queryClient.invalidateQueries({ queryKey: ['watchlist', userId] });
      setLastAction('watchlist');
      onActionComplete?.('watchlist', result.success);
    },
  });

  const toggleWatchlist = useCallback(async () => {
    watchlistMutation.mutate(!isInWatchlist);
  }, [isInWatchlist, watchlistMutation]);

  // Copy to clipboard
  const copyToClipboard = useCallback(async (asset: Asset): Promise<QuickActionResult> => {
    try {
      const text = `${asset.ticker} - ${asset.name}\n` +
        `Score: ${asset.score_total ? asset.score_total.toFixed(1) : 'N/A'}\n` +
        `Type: ${asset.asset_type}\n` +
        `Marché: ${asset.market_code}`;

      await navigator.clipboard.writeText(text);
      setLastAction('copy');
      onActionComplete?.('copy', true);
      return { success: true, message: 'Infos copiées' };
    } catch (error) {
      onActionComplete?.('copy', false);
      return {
        success: false,
        message: 'Impossible de copier',
      };
    }
  }, [onActionComplete]);

  // Share action
  const share = useCallback(async (asset: Asset): Promise<QuickActionResult> => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: `${asset.ticker} - ${asset.name}`,
          text: `Découvrez ${asset.name} (${asset.ticker}) sur MarketGPS avec un score de ${asset.score_total?.toFixed(1) || 'N/A'}`,
          url: `${window.location.origin}/asset/${asset.ticker}`,
        });
        setLastAction('share');
        onActionComplete?.('share', true);
        return { success: true, message: 'Partagé' };
      } else {
        // Fallback to copy link
        await navigator.clipboard.writeText(
          `${window.location.origin}/asset/${asset.ticker}`
        );
        onActionComplete?.('share', true);
        return { success: true, message: 'Lien copié' };
      }
    } catch (error) {
      onActionComplete?.('share', false);
      return {
        success: false,
        message: 'Impossible de partager',
      };
    }
  }, [onActionComplete]);

  return {
    // States
    isInWatchlist,
    lastAction,

    // Actions
    toggleWatchlist,
    copyToClipboard,
    share,

    // Loading states
    isToggling: watchlistMutation.isPending,
  };
}
