import { fireEvent, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import SettingsPage from '../../pages/SettingsPage';
import { AuthContext } from '../../context/authContextValue';
import { dashboardService } from '../../services/dashboardService';
import { makeAuth, renderWithProviders } from '../testUtils';

vi.mock('../../services/dashboardService', () => ({
  dashboardService: { getStats: vi.fn(), setAllRoastsVisibility: vi.fn() },
}));

const setVisibility = vi.mocked(dashboardService.setAllRoastsVisibility);

describe('SettingsPage', () => {
  it('calls the service once after confirming, and not on cancel', async () => {
    setVisibility.mockResolvedValue({ updated: 4 });
    renderWithProviders(
      <AuthContext.Provider value={makeAuth()}>
        <SettingsPage />
      </AuthContext.Provider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Make all my roasts private' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel' }));
    expect(setVisibility).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Make all my roasts private' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(setVisibility).toHaveBeenCalledTimes(1));
    expect(setVisibility).toHaveBeenCalledWith(false);
  });
});
