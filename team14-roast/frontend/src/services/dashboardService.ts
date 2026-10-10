import api from './api';
import type {
  DashboardRange,
  DashboardStats,
  VisibilityUpdateResult,
} from '../types/dashboard';

export const dashboardService = {
  async getStats(days: DashboardRange = 30): Promise<DashboardStats> {
    const { data } = await api.get<DashboardStats>('/dashboard/stats', { params: { days } });
    return data;
  },

  async setAllRoastsVisibility(isPublic: boolean): Promise<VisibilityUpdateResult> {
    const { data } = await api.put<VisibilityUpdateResult>('/settings/roasts-visibility', {
      is_public: isPublic,
    });
    return data;
  },
};
