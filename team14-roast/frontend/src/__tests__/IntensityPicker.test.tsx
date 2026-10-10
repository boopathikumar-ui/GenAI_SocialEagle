import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { IntensityPicker } from '../components/roast/IntensityPicker';
import { renderWithProviders } from './testUtils';

describe('IntensityPicker', () => {
  it('renders all options and marks the selected one', () => {
    renderWithProviders(<IntensityPicker value="medium" onChange={() => undefined} />);
    expect(screen.getAllByRole('radio')).toHaveLength(3);
    expect(screen.getByRole('radio', { name: 'Medium' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: 'Mild' })).toHaveAttribute('aria-checked', 'false');
  });

  it('calls onChange with the clicked intensity', () => {
    const onChange = vi.fn();
    renderWithProviders(<IntensityPicker value="mild" onChange={onChange} />);
    fireEvent.click(screen.getByRole('radio', { name: 'Spicy' }));
    expect(onChange).toHaveBeenCalledWith('spicy');
  });

  it('does not fire when disabled', () => {
    const onChange = vi.fn();
    renderWithProviders(<IntensityPicker value="mild" onChange={onChange} isDisabled />);
    fireEvent.click(screen.getByRole('radio', { name: 'Spicy' }));
    expect(onChange).not.toHaveBeenCalled();
  });
});
