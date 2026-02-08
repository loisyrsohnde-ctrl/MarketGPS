// ═══════════════════════════════════════════════════════════════════════════
// Gamification Types
// ═══════════════════════════════════════════════════════════════════════════

export interface GamificationProfile {
  user_id: string;
  level: number;
  current_xp: number;
  total_xp: number;
  points: number;
  streak_days: number;
  streak_multiplier: number;
  badges_earned: number;
  updated_at: string;
}

export interface Badge {
  badge_id: string;
  name: string;
  description: string;
  icon: string;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  earned: boolean;
  earned_at?: string;
  progress?: number;
  requirements?: string;
}

export interface Objective {
  objective_id: string;
  title: string;
  description: string;
  type: 'daily' | 'weekly';
  category: string;
  progress: number;
  target: number;
  reward_points: number;
  completed: boolean;
  completed_at?: string;
  expires_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  avatar_url?: string;
  level: number;
  total_points: number;
  badges_count: number;
  streak_days: number;
}

export interface GamificationAction {
  action_type: string;
  value?: number;
  description?: string;
}

export interface GamificationResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}
