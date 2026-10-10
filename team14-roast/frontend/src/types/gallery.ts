import type { Intensity, Paginated, ReactionEmoji, TargetType } from './index';

export type GallerySort = 'new' | 'top';

export type ReactionCounts = Record<ReactionEmoji, number>;

export interface GalleryRoast {
  id: number;
  github_username: string;
  target_type: TargetType;
  intensity: Intensity;
  roast_text: string;
  share_slug: string;
  created_at: string;
  reaction_counts: ReactionCounts;
  my_reactions: ReactionEmoji[];
}

export type GalleryPageData = Paginated<GalleryRoast>;

export interface ReactionState {
  reaction_counts: ReactionCounts;
  my_reactions: ReactionEmoji[];
}

export const REACTION_EMOJIS: readonly ReactionEmoji[] = ['fire', 'skull', 'laugh', 'clap'];

export const REACTION_GLYPHS: Record<ReactionEmoji, string> = {
  fire: '🔥',
  skull: '💀',
  laugh: '😂',
  clap: '👏',
};
