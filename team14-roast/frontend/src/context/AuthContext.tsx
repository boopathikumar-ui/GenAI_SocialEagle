import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { clearTokens } from '../services/api';
import { authService } from '../services/authService';
import type { User } from '../types';
import { AuthContext } from './authContextValue';
import type { AuthContextValue } from './authContextValue';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(authService.hasStoredSession());

  const refreshUser = useCallback(async (): Promise<void> => {
    try {
      setUser(await authService.getMe());
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    if (!authService.hasStoredSession()) return;
    let active = true;
    authService
      .getMe()
      .then((me) => {
        if (active) setUser(me);
      })
      .catch(() => {
        clearTokens();
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    const res = await authService.login({ email, password });
    setUser(res.user);
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string): Promise<void> => {
      const res = await authService.register({ email, password, full_name: fullName });
      setUser(res.user);
    },
    [],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
