'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X } from 'lucide-react';
import AIConcierge from './AIConcierge';

// =============================================================================
// Types
// =============================================================================

interface ConciergeFABProps {
  portfolioValue?: number;
  portfolioScore?: number;
  userName?: string;
  position?: 'bottom-right' | 'bottom-left';
  showPulse?: boolean;
}

// =============================================================================
// Main Component
// =============================================================================

export default function ConciergeFAB({
  portfolioValue,
  portfolioScore,
  userName,
  position = 'bottom-right',
  showPulse = true,
}: ConciergeFABProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  const handleOpen = () => {
    setIsOpen(true);
    setHasInteracted(true);
  };

  const positionClasses = {
    'bottom-right': 'right-6 bottom-6',
    'bottom-left': 'left-6 bottom-6',
  }[position];

  return (
    <>
      {/* Floating Action Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 1, type: 'spring', stiffness: 200 }}
        onClick={handleOpen}
        className={`
          fixed ${positionClasses} z-40
          w-14 h-14 rounded-2xl
          bg-gradient-to-br from-indigo-600 to-purple-600
          hover:from-indigo-500 hover:to-purple-500
          shadow-lg shadow-indigo-500/30
          flex items-center justify-center
          transition-all duration-300
          group
        `}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Pulse ring (only if not interacted) */}
        {showPulse && !hasInteracted && (
          <>
            <span className="absolute inset-0 rounded-2xl bg-indigo-500 animate-ping opacity-30" />
            <span className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-400 opacity-20 animate-pulse" />
          </>
        )}
        
        <Sparkles 
          size={24} 
          className="text-white group-hover:rotate-12 transition-transform" 
        />
        
        {/* Tooltip */}
        <AnimatePresence>
          {!isOpen && (
            <motion.div
              initial={{ opacity: 0, x: 10, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 10, scale: 0.9 }}
              className={`
                absolute ${position === 'bottom-right' ? 'right-full mr-3' : 'left-full ml-3'}
                whitespace-nowrap bg-slate-800 text-slate-200 text-sm font-medium
                px-3 py-2 rounded-lg shadow-lg border border-slate-700
                opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none
              `}
            >
              <div className="flex items-center gap-2">
                <span>Analyser ma stratégie</span>
                <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">IA</span>
              </div>
              {/* Arrow */}
              <div 
                className={`
                  absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-slate-800 border-slate-700 rotate-45
                  ${position === 'bottom-right' ? 'right-0 translate-x-1/2 border-r border-t' : 'left-0 -translate-x-1/2 border-l border-b'}
                `}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Concierge Modal */}
      <AIConcierge
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        portfolioValue={portfolioValue}
        portfolioScore={portfolioScore}
        userName={userName}
      />
    </>
  );
}
