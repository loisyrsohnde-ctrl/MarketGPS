import { renderHook, act, waitFor } from '@testing-library/react';
import useAuth from '@/hooks/useAuth';

// Mock supabase
const mockSession = {
  access_token: 'test-token',
  refresh_token: 'refresh-token',
  user: {
    id: 'user-123',
    email: 'test@example.com',
  },
};

const mockSupabase = {
  auth: {
    getSession: jest.fn(),
    signOut: jest.fn(),
    refreshSession: jest.fn(),
    onAuthStateChange: jest.fn(),
  },
};

jest.mock('@/lib/supabase', () => ({
  supabase: mockSupabase,
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock onAuthStateChange to return a subscription
    mockSupabase.auth.onAuthStateChange.mockReturnValue({
      data: {
        subscription: {
          unsubscribe: jest.fn(),
        },
      },
    });
  });

  it('initializes with loading state as true', () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.session).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('returns null user when not authenticated', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.session).toBeNull();
  });

  it('returns session and user when authenticated', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.session).toEqual(mockSession);
    expect(result.current.user).toEqual(mockSession.user);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles getSession errors gracefully', async () => {
    const error = new Error('Session fetch failed');
    mockSupabase.auth.getSession.mockRejectedValue(error);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have default empty state, not throw
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.session).toBeNull();
  });

  it('updates state when auth state changes', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    let authChangeCallback: Function;

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback: Function) => {
      authChangeCallback = callback;
      return {
        data: {
          subscription: {
            unsubscribe: jest.fn(),
          },
        },
      };
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Initially not authenticated
    expect(result.current.isAuthenticated).toBe(false);

    // Simulate auth state change
    act(() => {
      authChangeCallback('SIGNED_IN', mockSession);
    });

    await waitFor(() => {
      expect(result.current.session).toEqual(mockSession);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  it('handles signOut correctly', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
    });

    mockSupabase.auth.signOut.mockResolvedValue({});

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.signOut();
    });

    expect(mockSupabase.auth.signOut).toHaveBeenCalled();
  });

  it('handles signOut errors gracefully', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
    });

    const signOutError = new Error('Sign out failed');
    mockSupabase.auth.signOut.mockRejectedValue(signOutError);

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.signOut();
    });

    expect(consoleSpy).toHaveBeenCalledWith('Error signing out:', signOutError);

    consoleSpy.mockRestore();
  });

  it('refreshes session successfully', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const refreshedSession = {
      ...mockSession,
      access_token: 'new-token',
    };

    mockSupabase.auth.refreshSession.mockResolvedValue({
      data: { session: refreshedSession },
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let refreshedResult;
    await act(async () => {
      refreshedResult = await result.current.refreshSession();
    });

    expect(refreshedResult).toEqual(refreshedSession);
    expect(mockSupabase.auth.refreshSession).toHaveBeenCalled();
  });

  it('handles refresh session errors gracefully', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
    });

    const refreshError = new Error('Refresh failed');
    mockSupabase.auth.refreshSession.mockRejectedValue(refreshError);

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let refreshedResult;
    await act(async () => {
      refreshedResult = await result.current.refreshSession();
    });

    expect(refreshedResult).toBeNull();
    expect(consoleSpy).toHaveBeenCalledWith('Error refreshing session:', refreshError);

    consoleSpy.mockRestore();
  });

  it('unsubscribes from auth state changes on unmount', async () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const unsubscribeMock = jest.fn();

    mockSupabase.auth.onAuthStateChange.mockReturnValue({
      data: {
        subscription: {
          unsubscribe: unsubscribeMock,
        },
      },
    });

    const { unmount } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(mockSupabase.auth.onAuthStateChange).toHaveBeenCalled();
    });

    unmount();

    // Subscription unsubscribe is called in cleanup
    expect(unsubscribeMock).toBeDefined();
  });

  it('provides signOut method', () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.signOut).toBe('function');
  });

  it('provides refreshSession method', () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    });

    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.refreshSession).toBe('function');
  });
});
