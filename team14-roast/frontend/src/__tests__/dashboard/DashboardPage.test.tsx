import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DashboardPage from '../../pages/DashboardPage';
import { dashboardService } from '../../services/dashboardService';
import { renderWithProviders } from '../testUtils';
import { emptyStatsFixture, statsFixture } from './fixtures';

vi.mock('../../services/dashboardService', () => ({
  dashboardService: { getStats: vi.fn(), setAllRoastsVisibility: vi.fn() },
}));

const getStats = vi.mocked(dashboardService.getStats);

describe('DashboardPage', () => {
  beforeEach(() => {
    getStats.mockReset();
  });

  it('renders stats and refetches when the range changes', async () => {
    getStats.mockResolvedValue(statsFixture);
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByText('Reactions received')).toBeInTheDocument();
    expect(getStats).toHaveBeenLastCalledWith(30);
    fireEvent.click(screen.getByRole('button', { name: '7 days' }));
    await waitFor(() => expect(getStats).toHaveBeenLastCalledWith(7));
    expect(getStats).toHaveBeenCalledTimes(2);
  });

  it('shows an empty state for new users', async () => {
    getStats.mockResolvedValue(emptyStatsFixture);
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByText(/roast something first and your stats/i)).toBeInTheDocument();
  });

  it('shows an error and retries', async () => {
    getStats.mockRejectedValueOnce(new Error('boom')).mockResolvedValue(statsFixture);
    renderWithProviders(<DashboardPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('Reactions received')).toBeInTheDocument();
  });
});
