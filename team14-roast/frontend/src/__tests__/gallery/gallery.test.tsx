import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GalleryCard } from '../../components/gallery/GalleryCard';
import { ReactionBar } from '../../components/gallery/ReactionBar';
import { AuthContext } from '../../context/authContextValue';
import GalleryPage from '../../pages/GalleryPage';
import * as galleryService from '../../services/galleryService';
import type { GalleryRoast, ReactionCounts } from '../../types/gallery';
import { makeAuth } from '../testUtils';

vi.mock('../../services/galleryService');

const mocked = vi.mocked(galleryService);

const counts: ReactionCounts = { fire: 2, skull: 0, laugh: 1, clap: 0 };

function makeRoast(overrides: Partial<GalleryRoast> = {}): GalleryRoast {
  return {
    id: 7,
    github_username: 'octocat',
    target_type: 'profile',
    intensity: 'spicy',
    roast_text: 'Your commits are art.',
    share_slug: 'abc',
    created_at: '2026-01-01T00:00:00Z',
    reaction_counts: counts,
    my_reactions: [],
    ...overrides,
  };
}

function renderUi(ui: ReactElement, authed: boolean) {
  return render(
    <ChakraProvider>
      <AuthContext.Provider value={makeAuth({ isAuthenticated: authed })}>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthContext.Provider>
    </ChakraProvider>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe('ReactionBar', () => {
  it('toggles optimistically and applies server state', async () => {
    mocked.addReaction.mockResolvedValue({ reaction_counts: { ...counts, fire: 3 }, my_reactions: ['fire'] });
    renderUi(<ReactionBar roastId={7} counts={counts} mine={[]} />, true);
    const btn = screen.getByRole('button', { name: 'fire reaction, 2' });
    expect(btn).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(btn);
    expect(screen.getByRole('button', { name: 'fire reaction, 3' })).toHaveAttribute('aria-pressed', 'true');
    await waitFor(() => expect(mocked.addReaction).toHaveBeenCalledWith(7, 'fire'));
  });

  it('removes an active reaction via DELETE', async () => {
    mocked.removeReaction.mockResolvedValue({ reaction_counts: { ...counts, fire: 1 }, my_reactions: [] });
    renderUi(<ReactionBar roastId={7} counts={counts} mine={['fire']} />, true);
    fireEvent.click(screen.getByRole('button', { name: 'fire reaction, 2' }));
    await waitFor(() => expect(mocked.removeReaction).toHaveBeenCalledWith(7, 'fire'));
    expect(await screen.findByRole('button', { name: 'fire reaction, 1' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('rolls back when the request fails', async () => {
    mocked.addReaction.mockRejectedValue(new Error('boom'));
    renderUi(<ReactionBar roastId={7} counts={counts} mine={[]} />, true);
    fireEvent.click(screen.getByRole('button', { name: 'fire reaction, 2' }));
    await waitFor(() => expect(mocked.addReaction).toHaveBeenCalled());
    const rolled = await screen.findByRole('button', { name: 'fire reaction, 2' });
    expect(rolled).toHaveAttribute('aria-pressed', 'false');
  });

  it('prompts login and does not call the API when unauthenticated', async () => {
    renderUi(<ReactionBar roastId={7} counts={counts} mine={[]} />, false);
    fireEvent.click(screen.getByRole('button', { name: 'fire reaction, 2' }));
    const link = await screen.findByRole('link', { name: 'Log in' });
    expect(link).toHaveAttribute('href', '/login');
    expect(mocked.addReaction).not.toHaveBeenCalled();
  });
});

describe('GalleryCard', () => {
  it('renders roast text as plain text', () => {
    const evil = '<img src=x onerror="alert(1)"><script>alert(2)</script><b>bold</b>';
    const { container } = renderUi(<GalleryCard roast={makeRoast({ roast_text: evil })} />, false);
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('b')).toBeNull();
    expect(screen.getByText(evil)).toBeInTheDocument();
  });

  it('links to the full roast', () => {
    renderUi(<GalleryCard roast={makeRoast()} />, false);
    expect(screen.getByRole('link', { name: 'Read full roast' })).toHaveAttribute('href', '/r/abc');
  });
});

describe('GalleryPage', () => {
  it('refetches when the sort changes', async () => {
    mocked.listGallery.mockResolvedValue({ items: [makeRoast()], total: 1, page: 1, page_size: 12 });
    renderUi(<GalleryPage />, false);
    await screen.findByText('Your commits are art.');
    expect(mocked.listGallery).toHaveBeenLastCalledWith(1, 12, 'new');
    fireEvent.click(screen.getByRole('button', { name: 'Top' }));
    await waitFor(() => expect(mocked.listGallery).toHaveBeenLastCalledWith(1, 12, 'top'));
  });

  it('shows an empty state', async () => {
    mocked.listGallery.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 12 });
    renderUi(<GalleryPage />, false);
    expect(await screen.findByText(/No public roasts yet/)).toBeInTheDocument();
  });
});
