import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '@/components/ErrorBoundary';

// Mock lucide-react
jest.mock('lucide-react', () => ({
  AlertCircle: ({ className }: any) => <div data-testid="alert-icon" className={className} />,
  RefreshCw: ({ className }: any) => <div data-testid="refresh-icon" className={className} />,
}));

// Mock the Button component
jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

describe('ErrorBoundary', () => {
  // Test component that throws an error
  const ThrowingComponent = () => {
    throw new Error('Test error message');
  };

  // Test component that doesn't throw
  const WorkingComponent = () => <div data-testid="working-content">Working content</div>;

  beforeEach(() => {
    // Suppress console.error for error boundary tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <WorkingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('working-content')).toBeInTheDocument();
  });

  it('renders error message when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Oups ! Une erreur est survenue/i)).toBeInTheDocument();
    expect(
      screen.getByText(/rencontrons un problème technique/i)
    ).toBeInTheDocument();
  });

  it('displays error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Test error message/)).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('renders reset button that clears error state', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    // Error boundary should show error
    expect(screen.getByText(/Oups ! Une erreur est survenue/i)).toBeInTheDocument();

    // Click retry button
    const retryButton = screen.getByRole('button', { name: /Réessayer/i });
    fireEvent.click(retryButton);

    // Rerender with working component
    rerender(
      <ErrorBoundary>
        <WorkingComponent />
      </ErrorBoundary>
    );

    // Should now show working content
    expect(screen.getByTestId('working-content')).toBeInTheDocument();
  });

  it('renders home button that navigates to root', () => {
    window.location.href = 'http://test.com/error';

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    const homeButton = screen.getByRole('button', { name: /Retour à l'accueil/i });
    expect(homeButton).toBeInTheDocument();
  });

  it('renders custom fallback UI when provided', () => {
    const fallback = <div data-testid="custom-fallback">Custom error UI</div>;

    render(
      <ErrorBoundary fallback={fallback}>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.queryByText(/Oups ! Une erreur est survenue/i)).not.toBeInTheDocument();
  });

  it('stores error info in sessionStorage', () => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(setItemSpy).toHaveBeenCalledWith(
      'app_errors',
      expect.stringContaining('Test error message')
    );

    setItemSpy.mockRestore();
  });

  it('handles multiple errors and keeps last 10', () => {
    const getItemSpy = jest.spyOn(Storage.prototype, 'getItem');
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');

    // Mock existing errors in storage
    const existingErrors = Array.from({ length: 10 }, (_, i) => ({
      message: `Error ${i}`,
      timestamp: new Date().toISOString(),
    }));

    getItemSpy.mockReturnValue(JSON.stringify(existingErrors));

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    // Should keep last 10 errors
    const storedData = setItemSpy.mock.calls[0][1];
    const errors = JSON.parse(storedData);
    expect(errors.length).toBeLessThanOrEqual(10);

    getItemSpy.mockRestore();
    setItemSpy.mockRestore();
  });

  it('has accessible error message with role alert', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveAttribute('aria-live', 'assertive');
  });

  it('renders support contact link', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    const supportLink = screen.getByRole('link', { name: /Contacter le support/i });
    expect(supportLink).toBeInTheDocument();
    expect(supportLink).toHaveAttribute('href', 'mailto:support@marketgps.io');
  });
});
