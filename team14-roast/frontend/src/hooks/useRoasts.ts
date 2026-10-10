import { useCallback, useEffect, useState } from 'react';
import {
  createRoast,
  deleteRoast,
  getRoast,
  getSharedRoast,
  listRoasts,
  setRoastPublic,
  toRoastError,
} from '../services/roastService';
import type { RoastError } from '../services/roastService';
import type { CreateRoastRequest, Roast } from '../types';

export function useCreateRoast() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<RoastError | null>(null);

  const create = useCallback(async (req: CreateRoastRequest): Promise<Roast | null> => {
    setIsLoading(true);
    setError(null);
    try {
      return await createRoast(req);
    } catch (e) {
      setError(toRoastError(e));
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { create, isLoading, error, clearError };
}

interface FetchState {
  roast: Roast | null;
  isLoading: boolean;
  error: RoastError | null;
}

interface Settled {
  key: string | number;
  roast: Roast | null;
  error: RoastError | null;
}

function useFetchRoast(fetcher: () => Promise<Roast>, key: string | number | undefined): FetchState {
  const [settled, setSettled] = useState<Settled | null>(null);

  useEffect(() => {
    if (key === undefined) return;
    let cancelled = false;
    fetcher()
      .then((roast) => {
        if (!cancelled) setSettled({ key, roast, error: null });
      })
      .catch((e: unknown) => {
        if (!cancelled) setSettled({ key, roast: null, error: toRoastError(e) });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  if (key === undefined) return { roast: null, isLoading: false, error: null };
  if (settled === null || settled.key !== key) return { roast: null, isLoading: true, error: null };
  return { roast: settled.roast, isLoading: false, error: settled.error };
}

export function useRoast(id: number | undefined): FetchState {
  return useFetchRoast(() => getRoast(id as number), id);
}

export function useSharedRoast(slug: string | undefined): FetchState {
  return useFetchRoast(() => getSharedRoast(slug as string), slug);
}

export function useRoastList(pageSize = 10) {
  const [items, setItems] = useState<Roast[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPageState] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<RoastError | null>(null);

  useEffect(() => {
    let cancelled = false;
    listRoasts(page, pageSize)
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(toRoastError(e));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, pageSize]);

  const setPage = useCallback((p: number): void => {
    setIsLoading(true);
    setPageState(p);
  }, []);

  const remove = useCallback(async (id: number): Promise<void> => {
    try {
      await deleteRoast(id);
      setItems((prev) => prev.filter((r) => r.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (e) {
      setError(toRoastError(e));
    }
  }, []);

  const togglePublic = useCallback(async (id: number, isPublic: boolean): Promise<void> => {
    try {
      const updated = await setRoastPublic(id, isPublic);
      setItems((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (e) {
      setError(toRoastError(e));
    }
  }, []);

  return { items, total, page, pageSize, setPage, isLoading, error, remove, togglePublic };
}
