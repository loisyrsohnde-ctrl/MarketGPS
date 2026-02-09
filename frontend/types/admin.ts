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
