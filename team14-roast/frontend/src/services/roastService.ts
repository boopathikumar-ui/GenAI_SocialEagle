import axios from 'axios';
import api from './api';
import type { ApiErrorBody, CreateRoastRequest, Paginated, Roast } from '../types';

export async function createRoast(req: CreateRoastRequest): Promise<Roast> {
  const { data } = await api.post<Roast>('/roasts', req);
  return data;
}

export async function listRoasts(page = 1, pageSize = 10): Promise<Paginated<Roast>> {
  const { data } = await api.get<Paginated<Roast>>('/roasts', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getRoast(id: number): Promise<Roast> {
  const { data } = await api.get<Roast>(`/roasts/${id}`);
  return data;
}

export async function deleteRoast(id: number): Promise<void> {
  await api.delete(`/roasts/${id}`);
}

export async function setRoastPublic(id: number, isPublic: boolean): Promise<Roast> {
  const { data } = await api.patch<Roast>(`/roasts/${id}`, { is_public: isPublic });
  return data;
}

export async function getSharedRoast(slug: string): Promise<Roast> {
  const { data } = await api.get<Roast>(`/roasts/s/${encodeURIComponent(slug)}`);
  return data;
}

export type RoastErrorKind = 'invalid_url' | 'not_found' | 'rate_limited' | 'network' | 'server';

export interface RoastError {
  kind: RoastErrorKind;
  title: string;
  message: string;
}

export function toRoastError(err: unknown): RoastError {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    const status = err.response?.status;
    const envelope: unknown = err.response?.data?.error?.message;
    const legacy: unknown = err.response?.data?.detail;
    const detail: unknown = typeof envelope === 'string' && envelope ? envelope : legacy;
    if (!err.response) {
      return { kind: 'network', title: 'Cannot reach server', message: 'Check your connection and try again.' };
    }
    if (status === 429) {
      return { kind: 'rate_limited', title: 'Slow down, hot shot', message: 'Too many roasts too fast. Give the server a minute to cool off.' };
    }
    if (status === 404) {
      return { kind: 'not_found', title: 'Not found', message: typeof detail === 'string' ? detail : 'We could not find that GitHub user or roast.' };
    }
    if (status === 400 || status === 422) {
      return { kind: 'invalid_url', title: 'That URL does not look right', message: typeof detail === 'string' ? detail : 'Use a github.com profile or repository URL.' };
    }
  }
  return { kind: 'server', title: 'Our roaster burned out', message: 'Something went wrong on our side. Please try again shortly.' };
}

const GITHUB_URL_RE = /^https:\/\/(www\.)?github\.com\/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(\/[A-Za-z0-9._-]+)?\/?$/;

export function validateGithubUrl(value: string): string | null {
  const v = value.trim();
  if (!v) return 'Enter a GitHub profile or repo URL.';
  if (!GITHUB_URL_RE.test(v)) return 'Use a URL like https://github.com/username or https://github.com/username/repo';
  return null;
}

export function shareUrl(slug: string): string {
  return `${window.location.origin}/r/${slug}`;
}
