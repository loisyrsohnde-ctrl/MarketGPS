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
