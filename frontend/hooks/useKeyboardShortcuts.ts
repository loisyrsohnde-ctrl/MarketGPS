'use client';

import { useEffect } from 'react';

// ═══════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS HOOK
// ═══════════════════════════════════════════════════════════════════════════

interface KeyboardShortcuts {
  toggleWatchlist?: () => void;
  openAlert?: () => void;
  openComparator?: () => void;
  openAIChat?: () => void;
}

/**
 * Hook for managing keyboard shortcuts
 * W: Toggle watchlist
 * A: Open alert modal
 * C: Open comparator
 * I: Open AI chat
 */
export function useKeyboardShortcuts({
  toggleWatchlist,
  openAlert,
  openComparator,
  openAIChat,
}: KeyboardShortcuts) {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true'
      ) {
        return;
      }

      // Check for shortcuts (case-insensitive)
      const key = e.key.toLowerCase();

      if (e.altKey || e.ctrlKey || e.metaKey) return; // Don't interfere with browser shortcuts

      switch (key) {
        case 'w':
          e.preventDefault();
          toggleWatchlist?.();
          break;
        case 'a':
          e.preventDefault();
          openAlert?.();
          break;
        case 'c':
          e.preventDefault();
          openComparator?.();
          break;
        case 'i':
          e.preventDefault();
          openAIChat?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [toggleWatchlist, openAlert, openComparator, openAIChat]);
}

/**
 * Helper hook to show keyboard shortcuts help
 */
export function useShortcutsHelp() {
  const shortcuts = [
    { key: 'W', action: 'Toggle watchlist', icon: '📌' },
    { key: 'A', action: 'Open alert modal', icon: '🔔' },
    { key: 'C', action: 'Open comparator', icon: '📊' },
    { key: 'I', action: 'Open AI chat', icon: '🤖' },
  ];

  return shortcuts;
}
