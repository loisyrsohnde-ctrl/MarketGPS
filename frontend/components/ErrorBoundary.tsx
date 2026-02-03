'use client';

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

// ═══════════════════════════════════════════════════════════════════════════
// ERROR BOUNDARY COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);

    // Capture error details for debugging
    const errorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    };

    // TODO: Send to error tracking service (e.g., Sentry, LogRocket)
    if (typeof window !== 'undefined') {
      // Store in sessionStorage for debugging
      try {
        const errors = JSON.parse(sessionStorage.getItem('app_errors') || '[]');
        errors.push(errorDetails);
        sessionStorage.setItem('app_errors', JSON.stringify(errors.slice(-10)));
      } catch (e) {
        console.error('Failed to store error info:', e);
      }
    }

    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div
            role="alert"
            aria-live="assertive"
            className="min-h-screen flex items-center justify-center bg-bg-primary p-4"
          >
            <div className="max-w-md w-full">
              <div className="rounded-2xl border border-glass-border bg-bg-secondary p-8 shadow-lg">
                {/* Error Icon */}
                <div className="flex justify-center mb-6">
                  <div className="w-16 h-16 rounded-full bg-score-red/15 flex items-center justify-center">
                    <AlertCircle
                      className="w-8 h-8 text-score-red"
                      aria-hidden="true"
                    />
                  </div>
                </div>

                {/* Error Title */}
                <h1 className="text-2xl font-bold text-text-primary text-center mb-3">
                  Oups ! Une erreur est survenue
                </h1>

                {/* Error Message */}
                <p className="text-text-secondary text-center mb-6">
                  Nous rencontrons un problème technique. Veuillez rafraîchir la
                  page ou réessayer dans quelques instants.
                </p>

                {/* Error Details (Dev mode) */}
                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <div className="mb-6 p-4 rounded-xl bg-surface border border-glass-border">
                    <p className="text-xs font-mono text-text-muted break-words mb-2">
                      <span className="font-bold text-score-red">Erreur :</span>{' '}
                      {this.state.error.message}
                    </p>
                    {this.state.errorInfo?.componentStack && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-text-muted hover:text-text-secondary mb-2">
                          Stack trace
                        </summary>
                        <pre className="overflow-auto max-h-48 text-text-dim bg-bg-primary rounded p-2 border border-glass-border">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </details>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col gap-3">
                  <Button
                    onClick={this.handleReset}
                    variant="primary"
                    size="lg"
                    className="w-full"
                    aria-label="Réessayer après erreur"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Réessayer
                  </Button>

                  <Button
                    onClick={() => (window.location.href = '/')}
                    variant="secondary"
                    size="lg"
                    className="w-full"
                    aria-label="Retourner à la page d'accueil"
                  >
                    Retour à l'accueil
                  </Button>
                </div>

                {/* Support message */}
                <p className="text-xs text-text-muted text-center mt-6">
                  Si le problème persiste,{' '}
                  <a
                    href="mailto:support@marketgps.io"
                    className="text-accent hover:underline"
                    aria-label="Contacter le support"
                  >
                    contactez notre support
                  </a>
                </p>
              </div>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
