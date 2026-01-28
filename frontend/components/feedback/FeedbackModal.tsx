'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Star, Bug, Lightbulb, MessageCircle, HelpCircle, ThumbsUp, Loader2, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

type FeedbackType = 'general' | 'bug' | 'feature' | 'question' | 'praise';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  userEmail?: string;
  userId?: string;
}

const FEEDBACK_TYPES: { type: FeedbackType; label: string; icon: any; color: string }[] = [
  { type: 'general', label: 'Général', icon: MessageCircle, color: 'text-blue-400' },
  { type: 'bug', label: 'Bug', icon: Bug, color: 'text-red-400' },
  { type: 'feature', label: 'Idée', icon: Lightbulb, color: 'text-purple-400' },
  { type: 'question', label: 'Question', icon: HelpCircle, color: 'text-amber-400' },
  { type: 'praise', label: 'Bravo', icon: ThumbsUp, color: 'text-green-400' },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function FeedbackModal({ isOpen, onClose, userEmail, userId }: FeedbackModalProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('general');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [email, setEmail] = useState(userEmail || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setSubmitSuccess(false);
      setError(null);
    }
  }, [isOpen]);

  // Update email if userEmail prop changes
  useEffect(() => {
    if (userEmail) setEmail(userEmail);
  }, [userEmail]);

  const handleSubmit = async () => {
    if (!message.trim()) {
      setError('Veuillez entrer un message');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/feedback/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: feedbackType,
          subject: subject.trim() || null,
          message: message.trim(),
          rating,
          user_email: email.trim() || null,
          platform: 'web',
          app_version: '2.0.0',
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Échec de l\'envoi');
      }

      setSubmitSuccess(true);

      // Auto close after success
      setTimeout(() => {
        onClose();
        // Reset form
        setFeedbackType('general');
        setSubject('');
        setMessage('');
        setRating(null);
        setSubmitSuccess(false);
      }, 2000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="w-full max-w-lg bg-bg-secondary border border-glass-border rounded-2xl shadow-2xl pointer-events-auto overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-glass-border bg-surface/50">
                <h2 className="text-lg font-semibold text-text-primary">
                  Donnez-nous votre avis
                </h2>
                <button
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-5">
                {submitSuccess ? (
                  // Success State
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center justify-center py-10"
                  >
                    <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mb-4">
                      <CheckCircle className="w-8 h-8 text-accent" />
                    </div>
                    <h3 className="text-xl font-semibold text-text-primary mb-2">
                      Merci pour votre feedback !
                    </h3>
                    <p className="text-text-secondary text-center">
                      Nous l&apos;avons bien reçu et nous vous répondrons si nécessaire.
                    </p>
                  </motion.div>
                ) : (
                  <>
                    {/* Feedback Type Selection */}
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-3">
                        Type de feedback
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {FEEDBACK_TYPES.map(({ type, label, icon: Icon, color }) => (
                          <button
                            key={type}
                            onClick={() => setFeedbackType(type)}
                            className={cn(
                              'flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all',
                              feedbackType === type
                                ? 'bg-accent/20 text-accent border border-accent/50'
                                : 'bg-surface border border-glass-border text-text-secondary hover:bg-surface-hover'
                            )}
                          >
                            <Icon className={cn('w-4 h-4', feedbackType === type ? 'text-accent' : color)} />
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Subject (Optional) */}
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">
                        Sujet <span className="text-text-muted">(optionnel)</span>
                      </label>
                      <input
                        type="text"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        placeholder="Ex: Problème avec le graphique..."
                        className="w-full px-4 py-2.5 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-colors"
                      />
                    </div>

                    {/* Message */}
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">
                        Message <span className="text-score-red">*</span>
                      </label>
                      <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Décrivez votre feedback en détail..."
                        rows={4}
                        className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-colors resize-none"
                      />
                    </div>

                    {/* Rating */}
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">
                        Note globale <span className="text-text-muted">(optionnel)</span>
                      </label>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            onClick={() => setRating(rating === star ? null : star)}
                            className="p-1 transition-transform hover:scale-110"
                          >
                            <Star
                              className={cn(
                                'w-7 h-7 transition-colors',
                                rating && star <= rating
                                  ? 'fill-amber-400 text-amber-400'
                                  : 'text-text-muted hover:text-amber-400'
                              )}
                            />
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Email (for non-authenticated users) */}
                    {!userEmail && (
                      <div>
                        <label className="block text-sm font-medium text-text-secondary mb-2">
                          Votre email <span className="text-text-muted">(pour recevoir une réponse)</span>
                        </label>
                        <input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="email@example.com"
                          className="w-full px-4 py-2.5 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-colors"
                        />
                      </div>
                    )}

                    {/* Error */}
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 bg-score-red/10 border border-score-red/30 rounded-xl text-score-red text-sm"
                      >
                        {error}
                      </motion.div>
                    )}
                  </>
                )}
              </div>

              {/* Footer */}
              {!submitSuccess && (
                <div className="flex justify-end gap-3 px-6 py-4 border-t border-glass-border bg-surface/30">
                  <Button
                    variant="ghost"
                    onClick={handleClose}
                    disabled={isSubmitting}
                  >
                    Annuler
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={isSubmitting || !message.trim()}
                    className="min-w-[120px]"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Envoi...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Envoyer
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default FeedbackModal;
