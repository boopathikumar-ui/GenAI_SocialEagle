import axios from 'axios';
import api, { REFRESH_TOKEN_KEY, clearTokens, setTokens } from './api';
import type {
  ApiErrorBody,
  LoginRequest,
  RegisterRequest,
  TokenPair,
  UpdateProfileRequest,
  User,
} from '../types';

export interface AuthResponse extends TokenPair {
  user: User;
}

const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const GOOGLE_LOGIN_URL = `${API_URL}/api/v1/auth/google`;

interface ValidationDetail {
  msg: string;
}

function isValidationDetail(value: unknown): value is ValidationDetail {
  return typeof value === 'object' && value !== null && 'msg' in value;
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const envelope: unknown = error.response?.data?.error?.message;
    if (typeof envelope === 'string' && envelope) return envelope;
    const detail: unknown = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first: unknown = detail[0];
      if (isValidationDetail(first)) return String(first.msg);
    }
    if (!error.response) return 'Network error. Please try again.';
  }
  return fallback;
}

export const authService = {
  async register(payload: RegisterRequest): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/register', payload);
    setTokens(data);
    return data;
  },

  async login(payload: LoginRequest): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/login', payload);
    setTokens(data);
    return data;
  },

  async logout(): Promise<void> {
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
    try {
      if (refresh) await api.post('/auth/logout', { refresh_token: refresh });
    } finally {
      clearTokens();
    }
  },

  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  async updateMe(payload: UpdateProfileRequest): Promise<User> {
    const { data } = await api.put<User>('/auth/me', payload);
    return data;
  },

  hasStoredSession(): boolean {
    return localStorage.getItem(REFRESH_TOKEN_KEY) !== null;
  },
};
