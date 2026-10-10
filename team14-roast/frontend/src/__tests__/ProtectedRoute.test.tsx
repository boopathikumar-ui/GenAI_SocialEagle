import { screen } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import type { AuthContextValue } from '../context/authContextValue';
import type { User } from '../types';
import { makeAuth, renderWithProviders } from './testUtils';

const authState = vi.hoisted(() => ({ current: null as AuthContextValue | null }));

vi.mock('../hooks/useAuth', () => ({
  useAuth: (): AuthContextValue => {
    if (!authState.current) throw new Error('auth not set');
    return authState.current;
  },
}));

const user: User = {
  id: 1,
  email: 'a@example.com',
  full_name: 'A',
  is_active: true,
  is_verified: false,
  is_admin: false,
  oauth_provider: null,
  created_at: '2026-01-01T00:00:00Z',
};

function renderRoutes(route: string): void {
  renderWithProviders(
    <Routes>
      <Route path="/login" element={<div>login page</div>} />
      <Route element={<ProtectedRoute />}>
        <Route path="/roasts" element={<div>secret roasts</div>} />
      </Route>
    </Routes>,
    route,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    authState.current = makeAuth();
  });

  it('redirects anonymous users to /login', () => {
    renderRoutes('/roasts');
    expect(screen.getByText('login page')).toBeInTheDocument();
    expect(screen.queryByText('secret roasts')).toBeNull();
  });

  it('renders the protected content when authenticated', () => {
    authState.current = makeAuth({ user, isAuthenticated: true });
    renderRoutes('/roasts');
    expect(screen.getByText('secret roasts')).toBeInTheDocument();
  });

  it('shows a spinner (no content, no redirect) while loading', () => {
    authState.current = makeAuth({ isLoading: true });
    renderRoutes('/roasts');
    expect(screen.queryByText('secret roasts')).toBeNull();
    expect(screen.queryByText('login page')).toBeNull();
  });
});
