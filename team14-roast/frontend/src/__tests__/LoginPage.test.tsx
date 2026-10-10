import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuthContextValue } from '../context/authContextValue';
import LoginPage from '../pages/LoginPage';
import { makeAuth, renderWithProviders } from './testUtils';

const authState = vi.hoisted(() => ({ current: null as AuthContextValue | null }));

vi.mock('../hooks/useAuth', () => ({
  useAuth: (): AuthContextValue => {
    if (!authState.current) throw new Error('auth not set');
    return authState.current;
  },
}));

function fill(label: string, value: string): void {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

describe('LoginPage', () => {
  const login = vi.fn<(email: string, password: string) => Promise<void>>();

  beforeEach(() => {
    login.mockReset();
    login.mockResolvedValue(undefined);
    authState.current = makeAuth({ login });
  });

  it('shows validation errors and does not submit empty form', async () => {
    renderWithProviders(<LoginPage />, '/login');
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('rejects a malformed email', async () => {
    renderWithProviders(<LoginPage />, '/login');
    fill('Email', 'not-an-email');
    fill('Password', 'secret');
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('submits trimmed credentials when valid', async () => {
    renderWithProviders(<LoginPage />, '/login');
    fill('Email', ' me@example.com ');
    fill('Password', 'secret');
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    await waitFor(() => expect(login).toHaveBeenCalledWith('me@example.com', 'secret'));
  });

  it('shows a form error when login fails', async () => {
    login.mockRejectedValue(new Error('boom'));
    renderWithProviders(<LoginPage />, '/login');
    fill('Email', 'me@example.com');
    fill('Password', 'secret');
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
    expect(await screen.findByText('Login failed')).toBeInTheDocument();
  });
});
