'use client';

import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// INPUT COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  errorMessage?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, errorMessage, leftIcon, rightIcon, ariaLabel, ariaDescribedBy, id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = error ? `${inputId}-error` : undefined;
    const describedBy = [ariaDescribedBy, errorId].filter(Boolean).join(' ');

    return (
      <div className="relative w-full">
        {leftIcon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          type={type}
          className={cn(
            'flex h-12 w-full rounded-xl border bg-surface px-4 py-3 text-sm text-text-primary',
            'placeholder:text-text-muted',
            'transition-all duration-200',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error
              ? 'border-score-red focus:border-score-red focus:ring-score-red/15'
              : 'border-glass-border',
            leftIcon && 'pl-12',
            rightIcon && 'pr-12',
            className
          )}
          ref={ref}
          aria-label={ariaLabel}
          aria-describedby={describedBy || undefined}
          aria-invalid={error}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
            {rightIcon}
          </div>
        )}
        {error && errorMessage && (
          <p id={errorId} className="mt-2 text-sm text-score-red" role="alert">
            {errorMessage}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// ═══════════════════════════════════════════════════════════════════════════
// SEARCH INPUT COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

import { Search, X } from 'lucide-react';

export interface SearchInputProps extends Omit<InputProps, 'leftIcon' | 'rightIcon'> {
  onClear?: () => void;
}

const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, value, onClear, id, ...props }, ref) => {
    const inputId = id || `search-input-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="relative w-full">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" aria-hidden="true" />
        <input
          id={inputId}
          type="search"
          className={cn(
            'flex h-12 w-full rounded-xl border border-glass-border bg-surface pl-12 pr-12 py-3 text-sm text-text-primary',
            'placeholder:text-text-muted',
            'transition-all duration-200',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim',
            className
          )}
          ref={ref}
          value={value}
          aria-label="Rechercher"
          {...props}
        />
        {value && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors focus:outline-none focus:ring-2 focus:ring-accent-dim"
            aria-label="Effacer la recherche"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
    );
  }
);

SearchInput.displayName = 'SearchInput';

// ═══════════════════════════════════════════════════════════════════════════
// TEXTAREA COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
  errorMessage?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, errorMessage, ariaLabel, ariaDescribedBy, id, ...props }, ref) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = error ? `${textareaId}-error` : undefined;
    const describedBy = [ariaDescribedBy, errorId].filter(Boolean).join(' ');

    return (
      <div className="w-full">
        <textarea
          id={textareaId}
          className={cn(
            'flex min-h-[120px] w-full rounded-xl border bg-surface px-4 py-3 text-sm text-text-primary',
            'placeholder:text-text-muted',
            'transition-all duration-200',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'resize-none',
            error
              ? 'border-score-red focus:border-score-red focus:ring-score-red/15'
              : 'border-glass-border',
            className
          )}
          ref={ref}
          aria-label={ariaLabel}
          aria-describedby={describedBy || undefined}
          aria-invalid={error}
          {...props}
        />
        {error && errorMessage && (
          <p id={errorId} className="mt-2 text-sm text-score-red" role="alert">
            {errorMessage}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { Input, SearchInput, Textarea };
