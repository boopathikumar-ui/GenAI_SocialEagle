import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LanguagePicker } from '../components/roast/LanguagePicker';
import { renderWithProviders } from './testUtils';

describe('LanguagePicker', () => {
  it('offers English and Thanglish and marks the selected one', () => {
    renderWithProviders(<LanguagePicker value="english" onChange={() => undefined} />);
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    expect(screen.getByRole('radio', { name: 'English' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: 'Thanglish' })).toHaveAttribute('aria-checked', 'false');
  });

  it('calls onChange with the clicked language', () => {
    const onChange = vi.fn();
    renderWithProviders(<LanguagePicker value="english" onChange={onChange} />);
    fireEvent.click(screen.getByRole('radio', { name: 'Thanglish' }));
    expect(onChange).toHaveBeenCalledWith('thanglish');
  });

  it('does not fire when disabled', () => {
    const onChange = vi.fn();
    renderWithProviders(<LanguagePicker value="english" onChange={onChange} isDisabled />);
    fireEvent.click(screen.getByRole('radio', { name: 'Thanglish' }));
    expect(onChange).not.toHaveBeenCalled();
  });
});
