import { useCallback, useEffect, useState } from 'react';
import { listGallery } from '../services/galleryService';
import { toRoastError } from '../services/roastService';
import type { RoastError } from '../services/roastService';
import type { GalleryRoast, GallerySort } from '../types/gallery';

const PAGE_SIZE = 12;

interface UseGalleryResult {
  items: GalleryRoast[];
  total: number;
  isLoading: boolean;
  isLoadingMore: boolean;
  error: RoastError | null;
  hasMore: boolean;
  loadMore: () => void;
  retry: () => void;
}

interface Query {
  sort: GallerySort;
  page: number;
  nonce: number;
}

interface Result {
  /** Identifier of the query that produced this result. */
  key: string;
  sort: GallerySort;
  items: GalleryRoast[];
  total: number;
  error: RoastError | null;
}

const keyOf = (q: Query): string => `${q.sort}|${q.page}|${q.nonce}`;

export function useGallery(sort: GallerySort): UseGalleryResult {
  const [query, setQuery] = useState<Query>({ sort, page: 1, nonce: 0 });
  const [result, setResult] = useState<Result | null>(null);

  // A sort change always starts again from page 1.
  const effective: Query = query.sort === sort ? query : { sort, page: 1, nonce: query.nonce };
  const key = keyOf(effective);
  const { page, nonce } = effective;

  useEffect(() => {
    let cancelled = false;
    const q: Query = { sort, page, nonce };
    listGallery(page, PAGE_SIZE, sort)
      .then((res) => {
        if (cancelled) return;
        setResult((prev) => ({
          key: keyOf(q),
          sort,
          items: page === 1 || !prev || prev.sort !== sort ? res.items : [...prev.items, ...res.items],
          total: res.total,
          error: null,
        }));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setResult((prev) => ({
          key: keyOf(q),
          sort,
          items: prev && prev.sort === sort && page > 1 ? prev.items : [],
          total: prev && prev.sort === sort ? prev.total : 0,
          error: toRoastError(err),
        }));
      });
    return () => {
      cancelled = true;
    };
  }, [sort, page, nonce]);

  const settled = result !== null && result.key === key;
  const sameSort = result !== null && result.sort === sort;
  const items = sameSort && result ? result.items : [];
  const total = sameSort && result ? result.total : 0;

  const loadMore = useCallback(() => setQuery({ sort, page: page + 1, nonce }), [sort, page, nonce]);
  const retry = useCallback(() => setQuery({ sort, page, nonce: nonce + 1 }), [sort, page, nonce]);

  return {
    items,
    total,
    isLoading: !settled && page === 1,
    isLoadingMore: !settled && page > 1,
    error: settled && result ? result.error : null,
    hasMore: items.length < total,
    loadMore,
    retry,
  };
}
