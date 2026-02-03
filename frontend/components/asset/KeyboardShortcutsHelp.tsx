'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useShortcutsHelp } from '@/hooks/useKeyboardShortcuts';
import { HelpCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS HELP COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface KeyboardShortcutsHelpProps {
  className?: string;
}

export function KeyboardShortcutsHelp({ className }: KeyboardShortcutsHelpProps) {
  const [isOpen, setIsOpen] = useState(false);
  const shortcuts = useShortcutsHelp();

  return (
    <div className={className}>
      {/* Help button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        title="Raccourcis clavier disponibles"
        className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface transition-colors"
      >
        <HelpCircle className="w-5 h-5" />
      </motion.button>

      {/* Help popup */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute top-12 right-0 z-50 w-64 p-4 rounded-xl bg-bg-secondary border border-glass-border shadow-lg backdrop-blur-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text-primary">
                Raccourcis clavier
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              {shortcuts.map((shortcut, index) => (
                <motion.div
                  key={shortcut.key}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-2 rounded-lg bg-surface/50 border border-glass-border/50"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{shortcut.icon}</span>
                    <span className="text-xs text-text-secondary">{shortcut.action}</span>
                  </div>
                  <kbd className="px-2 py-1 rounded bg-surface border border-glass-border text-xs font-mono text-text-primary font-medium">
                    {shortcut.key}
                  </kbd>
                </motion.div>
              ))}
            </div>

            <p className="text-xs text-text-muted mt-4 pt-4 border-t border-glass-border">
              Appuyez sur les touches au-dessus pour activer les actions rapides
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default KeyboardShortcutsHelp;
