export type Intensity = 'mild' | 'medium' | 'spicy';
export type RoastLanguage = 'english' | 'thanglish';
export type TargetType = 'profile' | 'repo';
export type ReactionEmoji = 'fire' | 'skull' | 'laugh' | 'clap';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  oauth_provider: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface UpdateProfileRequest {
  full_name?: string | null;
}

export interface Roast {
  id: number;
  user_id: number | null;
  github_url: string;
  github_username: string;
  target_type: TargetType;
  intensity: Intensity;
  roast_text: string;
  is_public: boolean;
  share_slug: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRoastRequest {
  github_url: string;
  intensity: Intensity;
  is_public?: boolean;
  language?: RoastLanguage;
}

export interface Reaction {
  id: number;
  roast_id: number;
  user_id: number;
  emoji: ReactionEmoji;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiErrorBody {
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  /** Legacy FastAPI shape, kept as a fallback. */
  detail?: unknown;
}
