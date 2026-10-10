import { useCallback, useEffect, useState } from 'react';
import { dashboardService } from '../services/dashboardService';
import { getErrorMessage } from '../services/authService';
import type { DashboardRange, DashboardStats } from '../types/dashboard';

export interface UseDashboardResult {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  days: DashboardRange;
  setDays: (days: DashboardRange) => void;
  retry: () => void;
}

export function useDashboard(initialDays: DashboardRange = 30): UseDashboardResult {
  const [days, setDaysState] = useState<DashboardRange>(initialDays);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    dashboardService
      .getStats(days)
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(getErrorMessage(err, 'Could not load your dashboard'));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [days, attempt]);

  const setDays = useCallback((next: DashboardRange) => {
    setIsLoading(true);
    setError(null);
    setDaysState(next);
  }, []);

  const retry = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setAttempt((n) => n + 1);
  }, []);

  return { stats, isLoading, error, days, setDays, retry };
}
