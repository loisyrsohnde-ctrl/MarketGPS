'use client';

import { useState } from 'react';
import { MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { FeedbackModal } from './FeedbackModal';

// ═══════════════════════════════════════════════════════════════════════════
// FEEDBACK BUTTON - For sidebar/nav
// ═══════════════════════════════════════════════════════════════════════════

interface FeedbackButtonProps {
  collapsed?: boolean;
  userEmail?: string;
  userId?: string;
  className?: string;
}

export function FeedbackButton({ collapsed, userEmail, userId, className }: FeedbackButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={cn(
          'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl',
          'text-text-secondary hover:bg-accent/10 hover:text-accent',
          'transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-dim',
          className
        )}
        aria-label={collapsed ? 'Ouvrir formulaire de feedback' : undefined}
      >
        <MessageSquare className={cn('w-5 h-5', collapsed && 'mx-auto')} aria-hidden="true" />
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-sm font-medium"
            >
              Feedback
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      <FeedbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        userEmail={userEmail}
        userId={userId}
      />
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// FLOATING FEEDBACK BUTTON - Fixed position
// ═══════════════════════════════════════════════════════════════════════════

interface FloatingFeedbackButtonProps {
  userEmail?: string;
  userId?: string;
  position?: 'bottom-right' | 'bottom-left';
}

export function FloatingFeedbackButton({
  userEmail,
  userId,
  position = 'bottom-right'
}: FloatingFeedbackButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      <motion.button
        onClick={() => setIsModalOpen(true)}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={cn(
          'fixed z-40 flex items-center gap-2 px-4 py-3 rounded-full',
          'bg-accent text-bg-primary font-medium shadow-glow',
          'hover:bg-accent-light transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-bg-primary focus:ring-accent',
          position === 'bottom-right' ? 'right-6 bottom-6' : 'left-6 bottom-6'
        )}
        aria-label="Ouvrir formulaire de feedback"
      >
        <MessageSquare className="w-5 h-5" aria-hidden="true" />
        <AnimatePresence>
          {isHovered && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="text-sm whitespace-nowrap overflow-hidden"
              aria-hidden="true"
            >
              Feedback
            </motion.span>
          )}
        </AnimatePresence>
      </motion.button>

      <FeedbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        userEmail={userEmail}
        userId={userId}
      />
    </>
  );
}

export default FeedbackButton;
