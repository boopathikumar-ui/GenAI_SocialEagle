import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { RoastDisplay } from '../components/roast/RoastDisplay';
import type { Roast } from '../types';
import { renderWithProviders } from './testUtils';

function makeRoast(text: string): Roast {
  return {
    id: 1,
    user_id: null,
    github_url: 'https://github.com/octocat',
    github_username: 'octocat',
    target_type: 'profile',
    intensity: 'spicy',
    roast_text: text,
    is_public: true,
    share_slug: 'abc',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

describe('RoastDisplay', () => {
  it('shows username, intensity and text', () => {
    renderWithProviders(<RoastDisplay roast={makeRoast('Your commits are art.')} />);
    expect(screen.getByText('@octocat')).toBeInTheDocument();
    expect(screen.getByText('spicy')).toBeInTheDocument();
    expect(screen.getByText('profile')).toBeInTheDocument();
    expect(screen.getByText('Your commits are art.')).toBeInTheDocument();
  });

  it('renders HTML in roast text as plain text, never as elements', () => {
    const evil = '<img src=x onerror="alert(1)"><script>alert(2)</script><b>bold</b>';
    const { container } = renderWithProviders(<RoastDisplay roast={makeRoast(evil)} />);
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('b')).toBeNull();
    expect(screen.getByText(evil)).toBeInTheDocument();
  });

  it('escapes HTML in the username too', () => {
    const roast = { ...makeRoast('x'), github_username: '<i>sneaky</i>' };
    const { container } = renderWithProviders(<RoastDisplay roast={roast} />);
    expect(container.querySelector('i')).toBeNull();
  });
});
