import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const TOKEN_KEY = "data-explorer-tokens";
const USER_KEY = "data-explorer-user";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  roles: string[];
}

interface Tokens {
  access_token: string;
  refresh_token: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadTokens(): Tokens | null {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    return raw ? (JSON.parse(raw) as Tokens) : null;
  } catch {
    return null;
  }
}

function loadUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<Tokens | null>(loadTokens);
  const [user, setUser] = useState<AuthUser | null>(loadUser);
  const [isLoading, setIsLoading] = useState(false);

  const saveAuth = useCallback((t: Tokens, u: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(t));
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setTokens(t);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setTokens(null);
    setUser(null);
  }, []);

  const fetchUser = useCallback(
    async (accessToken: string): Promise<AuthUser> => {
      const res = await fetch(`${BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error("Failed to fetch user profile");
      return res.json();
    },
    [],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);
      try {
        const res = await fetch(`${BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Login failed");
        }
        // We only recieve a token not a user object, so we need to fetch the user object separately.
        const t: Tokens = await res.json();
        const u = await fetchUser(t.access_token);
        saveAuth(t, u);
      } finally {
        setIsLoading(false);
      }
    },
    [fetchUser, saveAuth],
  );

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      setIsLoading(true);
      try {
        const res = await fetch(`${BASE_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, name, password }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Registration failed");
        }
        const t: Tokens = await res.json();
        const u = await fetchUser(t.access_token);
        saveAuth(t, u);
      } finally {
        setIsLoading(false);
      }
    },
    [fetchUser, saveAuth],
  );

  const getAccessToken = useCallback(() => tokens?.access_token ?? null, [tokens]);

  // On mount, validate stored tokens
  useEffect(() => {
    if (!tokens) return;
    fetchUser(tokens.access_token).then(setUser).catch(() => logout());
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const value = useMemo<AuthContextValue>(
    () => ({ // Implicit return of an object
      user,
      tokens,
      isAuthenticated: !!user && !!tokens, // This is where isAuthenticated is set to true/false
      isLoading,
      login,
      register,
      logout,
      getAccessToken,
    }),
    [user, tokens, isLoading, login, register, logout, getAccessToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
