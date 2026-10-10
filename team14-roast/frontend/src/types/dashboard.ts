import type { Intensity } from './index';

export type DashboardRange = 7 | 30 | 90;

export interface DashboardTotals {
  roasts: number;
  public_roasts: number;
  reactions_received: number;
}

export interface RoastsPerDayPoint {
  date: string;
  count: number;
}

export type IntensitySplit = Record<Intensity, number>;

export interface LanguageCount {
  language: string;
  count: number;
}

export interface TopRoast {
  id: number;
  github_username: string;
  intensity: Intensity;
  share_slug: string;
  is_public: boolean;
  reaction_total: number;
  created_at: string;
}

export interface DashboardStats {
  totals: DashboardTotals;
  roasts_per_day: RoastsPerDayPoint[];
  intensity_split: IntensitySplit;
  top_languages: LanguageCount[];
  top_roasts: TopRoast[];
}

export interface VisibilityUpdateResult {
  updated: number;
}
