import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Paywall from '@/components/Paywall';

// Mock dependencies
jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

jest.mock('@/components/subscription/SubscriptionGate', () => ({
  SubscriptionRequired: ({ message, showLogin, gracePeriod }: any) => (
    <div data-testid="subscription-required">
      {message && <p>{message}</p>}
      {gracePeriod && <p>Grace period: {gracePeriod} hours</p>}
      {showLogin && <p>Show login prompt</p>}
    </div>
  ),
}));

import { useAuth } from '@/hooks/useAuth';
import { usePathname } from 'next/navigation';

describe('Paywall Component', () => {
  const mockUseAuth = useAuth as jest.Mock;
  const mockUsePathname = usePathname as jest.Mock;

  const TestChild = () => <div data-testid="test-child">Premium Content</div>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue('/dashboard');
    (global.fetch as jest.Mock).mockClear();
  });

  it('renders children when bypassing paywall in development', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('renders children on public news routes', async () => {
    mockUsePathname.mockReturnValue('/news');

    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });
  });

  it('shows subscription gate for unauthenticated users', async () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByTestId('subscription-required')).toBeInTheDocument();
      expect(
        screen.getByText(/Connectez-vous pour accéder à cette fonctionnalité/)
      ).toBeInTheDocument();
    });
  });

  it('shows login prompt for unauthenticated users', async () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByText('Show login prompt')).toBeInTheDocument();
    });
  });

  it('renders children for pro users with active subscription', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ is_active: true, plan: 'monthly' }),
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });
  });

  it('fetches subscription status when authenticated', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ is_active: true, plan: 'monthly' }),
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/billing/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
    });
  });

  it('shows paywall for users without active subscription', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ is_active: false, plan: 'free' }),
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByTestId('subscription-required')).toBeInTheDocument();
    });
  });

  it('shows grace period when applicable', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        is_active: false,
        plan: 'monthly',
        grace_period_remaining_hours: 24,
      }),
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByText('Grace period: 24 hours')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('handles network errors gracefully', async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: 'test-token' },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    );

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('shows loading content while checking auth', () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: true,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    // Should show children during loading
    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });

  it('handles localhost bypass', async () => {
    // Mock window.location
    const originalLocation = window.location;
    delete (window as any).location;
    (window as any).location = {
      hostname: 'localhost',
      href: 'http://localhost:3000',
    };

    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });

    // Restore location
    (window as any).location = originalLocation;
  });

  it('sends correct authorization header', async () => {
    const testToken = 'test-token-12345';

    mockUseAuth.mockReturnValue({
      session: { access_token: testToken },
      isLoading: false,
      isAuthenticated: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ is_active: true }),
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${testToken}`,
          }),
        })
      );
    });
  });

  it('does not fetch subscription when not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    await waitFor(() => {
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  it('respects bypass paywall env variable', () => {
    const originalEnv = process.env.NEXT_PUBLIC_BYPASS_PAYWALL;
    process.env.NEXT_PUBLIC_BYPASS_PAYWALL = 'true';

    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      isAuthenticated: false,
    });

    render(
      <Paywall>
        <TestChild />
      </Paywall>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();

    process.env.NEXT_PUBLIC_BYPASS_PAYWALL = originalEnv;
  });
});
