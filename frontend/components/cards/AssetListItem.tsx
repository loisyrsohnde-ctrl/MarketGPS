'use client';

import { cn } from '@/lib/utils';
import { AssetLogo } from '@/components/cards/asset-card';
import { ScoreGaugeBadge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';
import type { Asset } from '@/types';

// ═══════════════════════════════════════════════════════════════════════════
// ASSET LIST ITEM
// Responsive component: Card on mobile, table row on desktop
// ═══════════════════════════════════════════════════════════════════════════

interface AssetListItemProps {
  asset: Asset;
  index: number;
  onInspect: (ticker: string, assetId: string) => void;
}

export function AssetListItem({ asset, index, onInspect }: AssetListItemProps) {
  const handleClick = () => {
    onInspect(asset.ticker, asset.asset_id);
  };

  return (
    <>
      {/* ═══════════════════════════════════════════════════════════════════
         MOBILE CARD VIEW (hidden on md+)
         ═══════════════════════════════════════════════════════════════════ */}
      <div
        onClick={handleClick}
        className={cn(
          'md:hidden',
          'flex items-center gap-3 p-4',
          'bg-surface/30 rounded-xl border border-glass-border',
          'active:bg-surface/50 transition-colors',
          'cursor-pointer'
        )}
      >
        {/* Logo & Info */}
        <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="sm" />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-text-primary">{asset.ticker}</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-surface text-text-muted">
              {asset.asset_type}
            </span>
          </div>
          <p className="text-sm text-text-secondary truncate mt-0.5">{asset.name}</p>
        </div>

        {/* Score + Arrow */}
        <div className="flex items-center gap-2">
          {asset.score_total ? (
            <ScoreGaugeBadge score={asset.score_total} size="sm" />
          ) : (
            <span className="text-xs text-text-dim px-2">—</span>
          )}
          <ChevronRight className="w-5 h-5 text-text-muted" />
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
         DESKTOP TABLE ROW (hidden below md)
         ═══════════════════════════════════════════════════════════════════ */}
      <div
        className={cn(
          'hidden md:grid',
          'grid-cols-12 gap-4 p-4',
          'hover:bg-surface/50 transition-colors'
        )}
      >
        <div className="col-span-1 text-sm text-text-muted">{index}</div>
        <div
          className="col-span-2 flex items-center gap-2 cursor-pointer group"
          onClick={handleClick}
        >
          <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="xs" />
          <span className="font-semibold text-text-primary group-hover:text-accent transition-colors">
            {asset.ticker}
          </span>
        </div>
        <div className="col-span-4 text-sm text-text-secondary truncate">{asset.name}</div>
        <div className="col-span-1">
          <span className="px-2 py-0.5 rounded text-xs bg-surface text-text-muted">
            {asset.asset_type}
          </span>
        </div>
        <div className="col-span-2">
          {asset.score_total ? (
            <ScoreGaugeBadge score={asset.score_total} size="sm" />
          ) : (
            <span className="text-xs text-text-dim">—</span>
          )}
        </div>
        <div className="col-span-2 text-right">
          <Button variant="ghost" size="sm" onClick={handleClick}>
            Inspecter
          </Button>
        </div>
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// ASSET LIST SKELETON
// Responsive skeleton: Card on mobile, row on desktop
// ═══════════════════════════════════════════════════════════════════════════

export function AssetListSkeleton() {
  return (
    <>
      {/* Mobile skeleton */}
      <div className="md:hidden flex items-center gap-3 p-4 bg-surface/30 rounded-xl border border-glass-border">
        <div className="w-10 h-10 rounded-lg skeleton" />
        <div className="flex-1">
          <div className="h-4 w-20 skeleton rounded mb-2" />
          <div className="h-3 w-32 skeleton rounded" />
        </div>
        <div className="h-6 w-12 skeleton rounded" />
      </div>

      {/* Desktop skeleton */}
      <div className="hidden md:grid grid-cols-12 gap-4 p-4">
        <div className="col-span-1">
          <div className="h-4 w-8 skeleton rounded" />
        </div>
        <div className="col-span-2">
          <div className="h-4 w-16 skeleton rounded" />
        </div>
        <div className="col-span-4">
          <div className="h-4 w-48 skeleton rounded" />
        </div>
        <div className="col-span-1">
          <div className="h-4 w-12 skeleton rounded" />
        </div>
        <div className="col-span-2">
          <div className="h-6 w-12 skeleton rounded" />
        </div>
        <div className="col-span-2">
          <div className="h-8 w-20 skeleton rounded ml-auto" />
        </div>
      </div>
    </>
  );
}

export default AssetListItem;
