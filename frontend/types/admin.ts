export interface AdminStats {
  users: {
    total: number;
    pro: number;
    free: number;
    newToday: number;
    newThisWeek: number;
  };
  news: {
    scrapedToday: number;
    viralCount: number;
    scriptsGenerated: number;
  };
  system: {
    lastPipelineRun: string;
    sourcesActive: number;
    llm_provider?: string;
  };
}

export interface ViralArticle {
  id: string;
  title: string;
  source: string;
  region: string;
  language: string;
  interactions: number;
  viralityScore: number;
  publishedAt: string;
  hasScript: boolean;
  url?: string;
  thumbnail?: string;
}

export interface VideoScript {
  id: string;
  articleId: string;
  title: string;
  hook: string;
  scriptText: string;
  wordCount: number;
  estimatedDuration: number;
  status: 'draft' | 'reviewed' | 'approved' | 'published';
  createdAt: string;
  updatedAt: string;
  articleTitle?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  plan: 'free' | 'pro' | 'enterprise';
  createdAt: string;
  lastLogin: string;
  isActive: boolean;
}

export interface EditorialComponentScores {
  source_diversity: number;
  verified_engagement: number;
  topic_importance: number;
  freshness: number;
  geo_relevance: number;
}

export interface EditorialArticle {
  article_id: number;
  title: string | null;
  source_name: string | null;
  editorial_score: number;
  reasons: string[];
  component_scores: EditorialComponentScores;
  cluster_id: string | null;
  cluster_size: number;
  cluster_sources: string[];
  scored_at: string | null;
  country: string | null;
  language: string | null;
  published_at: string | null;
  url: string | null;
  total_interactions: number | null;
}

export interface EditorialScoresResponse {
  articles: EditorialArticle[];
  total: number;
  updated_at: string;
}

export interface YouTubeScriptSection {
  section: string;
  duration_seconds: number;
  title: string;
  content: string;
}

export interface YouTubeScript {
  id: string;
  articleId: string;
  titleSuggestions: string[];
  description: string;
  tags: string[];
  scriptSections: YouTubeScriptSection[];
  totalWordCount: number;
  keyStatistics: Array<{
    stat: string;
    source: string;
  }>;
  thumbnailSuggestions: string[];
  status: 'draft' | 'reviewed' | 'approved' | 'published';
  createdAt: string;
  updatedAt: string;
}

export interface TitleVariant {
  variant: string;
  approach: string;
}

export interface SocialMetadata {
  id: string;
  articleId: string;
  titleVariants: TitleVariant[];
  description: string;
  hashtags: string[];
  thumbnailTextOptions: string[];
  seoKeywords: string[];
  createdAt: string;
  updatedAt: string;
}

// ═══════════════════════════════════════════════════════════════
// Subscriptions
// ═══════════════════════════════════════════════════════════════

export interface Subscription {
  user_id: string;
  email: string | null;
  full_name: string | null;
  plan: string;
  status: string;
  amount: number | null;
  currency: string | null;
  interval: string | null;
  created_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  payment_method: string | null;
}

// ═══════════════════════════════════════════════════════════════
// Feedbacks
// ═══════════════════════════════════════════════════════════════

export interface Feedback {
  id: string;
  type: string;
  subject: string | null;
  message: string;
  user_email: string | null;
  rating: number | null;
  platform: string | null;
  status: string;
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════
// AI Quotas
// ═══════════════════════════════════════════════════════════════

export interface AIQuota {
  user_id: string;
  provider: string;
  usage_count: number;
  limit: number;
  limit_disabled: boolean;
  last_used: string | null;
}

export interface AIQuotaUser {
  user_id: string;
  quotas: AIQuota[];
}

// ═══════════════════════════════════════════════════════════════
// Diagnostics
// ═══════════════════════════════════════════════════════════════

export interface DiagnosticsData {
  timestamp: string;
  universe: {
    total: number;
    by_scope: Record<string, number>;
    active_by_scope: Record<string, number>;
    by_type: Record<string, number>;
    error?: string;
  };
  scores: {
    total_scored: number;
    by_scope: Record<string, number>;
    last_update: string | null;
    distribution: {
      high_70_plus: number;
      medium_40_69: number;
      low_below_40: number;
    };
    error?: string;
  };
  news: {
    total_articles: number;
    by_region: Record<string, number>;
    last_article_created: string | null;
    last_article_published: string | null;
    articles_today: number;
    articles_this_week: number;
    error?: string;
  };
  strategies: {
    templates_count: number;
    user_strategies_count: number;
    error?: string;
  };
  watchlist: {
    total_items: number;
    unique_users: number;
    error?: string;
  };
}

export interface PipelineStatus {
  scheduler_configured: boolean;
  last_run: string | null;
  last_success: string | null;
  last_result: Record<string, unknown> | null;
  history: Record<string, unknown>[];
  sources_configured: number;
  minutes_since_last_run?: number;
  is_stale?: boolean;
}

export interface RegionalImpact {
  africa: string;
  global: string;
}

export interface AddedStatistic {
  statistic: string;
  context: string;
  source?: string;
}

export interface EnrichedArticle {
  id: string;
  originalArticleId: string;
  enrichedContent: string;
  addedStatistics: AddedStatistic[];
  historicalContext: string;
  regionalImpact: RegionalImpact;
  keyActors: string[];
  futureImplications: string;
  createdAt: string;
}

// ═══════════════════════════════════════════════════════════════
// Workflow
// ═══════════════════════════════════════════════════════════════

export type EditorialStatusType = 'pending' | 'researched' | 'rewritten' | 'approved' | 'published' | 'rejected';

export interface WorkflowArticle {
  id: string;
  title: string;
  content_md: string | null;
  summary: string | null;
  source_name: string;
  source_url: string | null;
  published_at: string | null;
  country: string | null;
  language: string | null;
  category: string | null;
  total_interactions: number;
  editorial_status: EditorialStatusType;
  french_content_md: string | null;
  editorial_notes: string | null;
  approved_at: string | null;
  approved_by: string | null;
  image_url: string | null;
  editorial_score: number | null;
  component_scores: EditorialComponentScores | null;
}

export interface WorkflowStep {
  step: 1 | 2 | 3 | 4;
  label: string;
  status: 'pending' | 'active' | 'completed';
}

// ═══════════════════════════════════════════════════════════════
// Global Search
// ═══════════════════════════════════════════════════════════════

export interface SearchResult {
  id: string;
  type: 'article' | 'script' | 'user';
  title: string;
  subtitle: string;
  snippet: string;
  score: number;
  metadata: Record<string, string | number>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  took_ms: number;
}

// ═══════════════════════════════════════════════════════════════
// Activity Log
// ═══════════════════════════════════════════════════════════════

export interface ActivityLogEntry {
  id: number;
  admin_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: string | null;
  changes_json: Record<string, unknown> | null;
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════
// News Source Management
// ═══════════════════════════════════════════════════════════════

export interface NewsSource {
  name: string;
  url: string;
  rss_url: string;
  type: 'rss' | 'scraper';
  country: string | null;
  region: string;
  language: string;
  tags: string[];
  trust_score: number;
  enabled: boolean;
  articles_this_week?: number;
  last_scraped_at?: string;
}

// ═══════════════════════════════════════════════════════════════
// Admin Settings
// ═══════════════════════════════════════════════════════════════

export interface AdminSettings {
  editorial: {
    virality_threshold_2x: number;
    virality_threshold_5x: number;
    virality_threshold_10x: number;
    min_editorial_score: number;
    rewrite_model: 'openai' | 'gemini';
    rewrite_temperature: number;
    editorial_line: string;
  };
  notifications: {
    alert_on_viral_break: boolean;
    viral_threshold: number;
    alert_channels: string[];
    webhook_url: string;
  };
  maintenance: {
    is_under_maintenance: boolean;
    maintenance_message: string;
    api_rate_limit: number;
  };
  scraping: {
    enable_automatic_ingestion: boolean;
    max_articles_per_source: number;
    daily_ingest_times: string[];
  };
}

// ═══════════════════════════════════════════════════════════════
// Dashboard Metrics
// ═══════════════════════════════════════════════════════════════

export interface DashboardMetrics {
  pipeline: {
    articles_today: number;
    articles_week: number;
    viral_count: number;
    published_count: number;
    in_workflow: Record<EditorialStatusType, number>;
    trend_7d: { date: string; count: number }[];
  };
  geography: {
    by_country: { country: string; count: number; interactions: number }[];
  };
  editorial: {
    avg_score: number;
    top_topics: { topic: string; count: number }[];
    source_diversity: number;
  };
  system: {
    last_pipeline_run: string | null;
    sources_active: number;
    llm_provider: string | null;
    db_size_mb: number;
  };
  recent_activity: ActivityLogEntry[];
}
