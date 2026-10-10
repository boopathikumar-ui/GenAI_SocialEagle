import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { IntensityChart } from '../../components/dashboard/IntensityChart';
import { LanguagesChart } from '../../components/dashboard/LanguagesChart';
import { RoastsPerDayChart } from '../../components/dashboard/RoastsPerDayChart';
import { renderWithProviders } from '../testUtils';
import { emptyStatsFixture, statsFixture } from './fixtures';

describe('dashboard charts', () => {
  it('summarizes roasts per day and exposes a table', () => {
    renderWithProviders(<RoastsPerDayChart data={statsFixture.roasts_per_day} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent(
      '5 roasts over 3 days. Busiest day: 2026-10-09 with 3.',
    );
    expect(screen.getByRole('img', { name: /roasts per day/i })).toBeInTheDocument();
    expect(screen.getAllByRole('row')).toHaveLength(4);
  });

  it('handles an all-zero series', () => {
    renderWithProviders(<RoastsPerDayChart data={emptyStatsFixture.roasts_per_day} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent('No roasts in this period.');
  });

  it('summarizes intensity split, including all zero', () => {
    const { unmount } = renderWithProviders(<IntensityChart data={statsFixture.intensity_split} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent(
      'Mild 1 (20%), Medium 1 (20%), Spicy 3 (60%)',
    );
    unmount();
    renderWithProviders(<IntensityChart data={emptyStatsFixture.intensity_split} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent('No roasts in this period.');
  });

  it('summarizes languages and handles empty', () => {
    const { unmount } = renderWithProviders(<LanguagesChart data={statsFixture.top_languages} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent('Top language: Python (3)');
    unmount();
    renderWithProviders(<LanguagesChart data={[]} />);
    expect(screen.getByTestId('chart-summary')).toHaveTextContent('No language data yet.');
  });
});
