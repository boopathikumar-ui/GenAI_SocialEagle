import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatCard } from '../../components/dashboard/StatCard';
import { renderWithProviders } from '../testUtils';

describe('StatCard', () => {
  it('renders label and formatted value', () => {
    renderWithProviders(<StatCard label="Roasts" value={1234} />);
    expect(screen.getByText('Roasts')).toBeInTheDocument();
    expect(screen.getByTestId('stat-value')).toHaveTextContent('1,234');
  });

  it('renders zero', () => {
    renderWithProviders(<StatCard label="Public roasts" value={0} />);
    expect(screen.getByTestId('stat-value')).toHaveTextContent('0');
  });
});
