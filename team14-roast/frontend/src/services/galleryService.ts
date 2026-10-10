import api from './api';
import type { ReactionEmoji } from '../types';
import type { GalleryPageData, GallerySort, ReactionState } from '../types/gallery';

export async function listGallery(page: number, pageSize: number, sort: GallerySort): Promise<GalleryPageData> {
  const { data } = await api.get<GalleryPageData>('/gallery', {
    params: { page, page_size: pageSize, sort },
  });
  return data;
}

export async function addReaction(roastId: number, emoji: ReactionEmoji): Promise<ReactionState> {
  const { data } = await api.post<ReactionState>(`/roasts/${roastId}/reactions`, { emoji });
  return data;
}

export async function removeReaction(roastId: number, emoji: ReactionEmoji): Promise<ReactionState> {
  const { data } = await api.delete<ReactionState>(
    `/roasts/${roastId}/reactions/${encodeURIComponent(emoji)}`,
  );
  return data;
}
