/**
 * Local Authentication - Development mode
 * Simple in-memory auth for local development without Supabase
 */

interface User {
  id: string;
  email: string;
  name?: string;
}

interface LocalAuthSession {
  user: User;
  token: string;
}

// In-memory user store (in production, this would be a real database)
const USERS_STORE: Record<string, { email: string; password: string; name?: string }> = {
  'demo@example.com': { email: 'demo@example.com', password: 'demo123', name: 'Demo User' },
  'test@example.com': { email: 'test@example.com', password: 'test123', name: 'Test User' },
};

export const localAuth = {
  /**
   * Sign in with email and password
   */
  signIn: async (email: string, password: string): Promise<LocalAuthSession> => {
    const user = USERS_STORE[email];

    if (!user || user.password !== password) {
      throw new Error('Identifiants invalides');
    }

    const token = Buffer.from(`${email}:${Date.now()}`).toString('base64');

    return {
      user: {
        id: email,
        email: user.email,
        name: user.name,
      },
      token,
    };
  },

  /**
   * Sign up with email and password
   */
  signUp: async (email: string, password: string, name?: string): Promise<LocalAuthSession> => {
    if (USERS_STORE[email]) {
      throw new Error('Cet email est déjà utilisé');
    }

    USERS_STORE[email] = { email, password, name };

    const token = Buffer.from(`${email}:${Date.now()}`).toString('base64');

    return {
      user: {
        id: email,
        email,
        name,
      },
      token,
    };
  },

  /**
   * Get current session from localStorage
   */
  getSession: async (): Promise<LocalAuthSession | null> => {
    if (typeof window === 'undefined') return null;

    const sessionStr = localStorage.getItem('marketgps_session');
    if (!sessionStr) return null;

    try {
      return JSON.parse(sessionStr);
    } catch {
      return null;
    }
  },

  /**
   * Save session to localStorage
   */
  saveSession: (session: LocalAuthSession) => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('marketgps_session', JSON.stringify(session));
  },

  /**
   * Clear session
   */
  clearSession: () => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('marketgps_session');
  },

  /**
   * Get current user
   */
  getCurrentUser: async (): Promise<User | null> => {
    const session = await localAuth.getSession();
    return session?.user || null;
  },
};

export type { LocalAuthSession, User };
