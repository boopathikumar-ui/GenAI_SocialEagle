import type { DashboardStats } from '../../types/dashboard';

export const statsFixture: DashboardStats = {
  totals: { roasts: 5, public_roasts: 2, reactions_received: 9 },
  roasts_per_day: [
    { date: '2026-10-08', count: 1 },
    { date: '2026-10-09', count: 3 },
    { date: '2026-10-10', count: 1 },
  ],
  intensity_split: { mild: 1, medium: 1, spicy: 3 },
  top_languages: [
    { language: 'Python', count: 3 },
    { language: 'Go', count: 2 },
  ],
  top_roasts: [
    {
      id: 7,
      github_username: 'octocat',
      intensity: 'spicy',
      share_slug: 'abc123',
      is_public: true,
      reaction_total: 6,
      created_at: '2026-10-09T10:00:00Z',
    },
  ],
};

export const emptyStatsFixture: DashboardStats = {
  totals: { roasts: 0, public_roasts: 0, reactions_received: 0 },
  roasts_per_day: [
    { date: '2026-10-09', count: 0 },
    { date: '2026-10-10', count: 0 },
  ],
  intensity_split: { mild: 0, medium: 0, spicy: 0 },
  top_languages: [],
  top_roasts: [],
};
