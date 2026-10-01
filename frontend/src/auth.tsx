import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { api, setShareToken } from './api';
import type { Role } from './api';

interface AuthState {
  role: Role;
  login: string | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  role: 'anonymous',
  login: null,
  loading: true,
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>('anonymous');
  const [login, setLogin] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await api.me();
      setRole(me.role);
      setLogin(me.github_login);
      if (me.role === 'owner') {
        // A saved share token is irrelevant once the owner is logged in.
        localStorage.removeItem('shareToken');
        setShareToken(null);
      }
    } catch {
      setRole('anonymous');
      setLogin(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(() => ({ role, login, loading, refresh }), [role, login, loading, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
