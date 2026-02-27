'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X, ChevronRight, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/config';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface BreakingNewsItem {
  id: number;
  slug: string;
  title: string;
  excerpt: string | null;
  source_name: string;
  published_at: string | null;
  engagement_score: number;
  importance_level: string;
  category: string | null;
  country: string | null;
}

interface BreakingNewsResponse {
  data: BreakingNewsItem[];
  count: number;
  has_breaking: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = getApiBaseUrl();

async function fetchBreakingNews(): Promise<BreakingNewsResponse> {
  const res = await fetch(`${API_BASE}/api/news/breaking?limit=5&max_age_hours=6`);
  if (!res.ok) return { data: [], count: 0, has_breaking: false };
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Time Helper
// ═══════════════════════════════════════════════════════════════════════════

function getTimeAgo(publishedAt: string | null): string {
  if (!publishedAt) return '';

  try {
    const published = new Date(publishedAt);
    const now = new Date();
    const diffMs = now.getTime() - published.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Il y a ${diffHours}h`;

    return published.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', timeZone: 'UTC' });
  } catch {
    return '';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Breaking News Banner Component
// ═══════════════════════════════════════════════════════════════════════════

interface BreakingNewsBannerProps {
  className?: string;
  autoRotate?: boolean;
  rotateInterval?: number;
}

export default function BreakingNewsBanner({
  className,
  autoRotate = true,
  rotateInterval = 8000
}: BreakingNewsBannerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDismissed, setIsDismissed] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['breaking-news'],
    queryFn: fetchBreakingNews,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });

  // Auto-rotate through breaking news
  useEffect(() => {
    if (!autoRotate || !data?.data.length || data.data.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % data.data.length);
    }, rotateInterval);

    return () => clearInterval(interval);
  }, [autoRotate, rotateInterval, data?.data.length]);

  // Don't render if no breaking news or dismissed
  if (isLoading || !data?.has_breaking || isDismissed) {
    return null;
  }

  const currentItem = data.data[currentIndex];
  if (!currentItem) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: 'auto', opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        className={cn(
          'relative bg-gradient-to-r from-red-600 to-red-700 text-white overflow-hidden',
          className
        )}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 py-3">
            {/* Breaking Badge */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className="relative">
                <AlertCircle className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-white rounded-full animate-ping" />
              </div>
              <span className="hidden sm:inline font-bold text-sm uppercase tracking-wider">
                Alerte Info
              </span>
            </div>

            {/* Divider */}
            <div className="h-6 w-px bg-red-400 flex-shrink-0" />

            {/* Content */}
            <Link
              href={`/news/${currentItem.slug}`}
              className="flex-1 min-w-0 group"
            >
              <motion.div
                key={currentItem.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-4"
              >
                <p className="font-medium text-sm md:text-base truncate group-hover:underline">
                  {currentItem.title}
                </p>
                <div className="hidden md:flex items-center gap-2 text-xs text-red-200 flex-shrink-0">
                  <span>{currentItem.source_name}</span>
                  <span>•</span>
                  <span>{getTimeAgo(currentItem.published_at)}</span>
                </div>
                <ChevronRight className="w-4 h-4 flex-shrink-0 group-hover:translate-x-1 transition-transform" />
              </motion.div>
            </Link>

            {/* Counter (if multiple) */}
            {data.data.length > 1 && (
              <div className="hidden sm:flex items-center gap-1 flex-shrink-0">
                {data.data.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentIndex(idx)}
                    className={cn(
                      'w-2 h-2 rounded-full transition-colors',
                      idx === currentIndex ? 'bg-white' : 'bg-red-400 hover:bg-red-300'
                    )}
                  />
                ))}
              </div>
            )}

            {/* Dismiss Button */}
            <button
              onClick={() => setIsDismissed(true)}
              className="p-1 hover:bg-red-500 rounded transition-colors flex-shrink-0"
              aria-label="Fermer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Compact Breaking News Badge (for use in sidebars, etc.)
// ═══════════════════════════════════════════════════════════════════════════

export function BreakingNewsBadge({ className }: { className?: string }) {
  const { data } = useQuery({
    queryKey: ['breaking-news'],
    queryFn: fetchBreakingNews,
    staleTime: 30000,
    refetchInterval: 60000,
  });

  if (!data?.has_breaking) return null;

  return (
    <Link href="/news" className={cn('block', className)}>
      <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors">
        <div className="relative">
          <Bell className="w-4 h-4 text-red-600" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-600 rounded-full animate-pulse" />
        </div>
        <span className="text-sm font-medium text-red-700">
          {data.count} alerte{data.count > 1 ? 's' : ''} info
        </span>
      </div>
    </Link>
  );
}
