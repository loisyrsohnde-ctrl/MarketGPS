import { NextResponse } from 'next/server';
import type { NewsItem } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/news/digest
// Returns news digest with breaking and important news
// ═══════════════════════════════════════════════════════════════════════════

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '5';

    // TODO: Fetch from backend API or database
    // For now, return mock data
    const mockNews: { breaking: NewsItem[]; important: NewsItem[] } = {
      breaking: [
        {
          id: '1',
          title: 'Fed Signals Potential Rate Pause in 2024',
          summary: 'Federal Reserve officials indicate a pause in interest rate hikes...',
          source: 'Reuters',
          url: 'https://reuters.com',
          sentiment: 'positive',
          tickers: ['SPY', 'QQQ', 'IVV'],
          isBreaking: true,
          importance: 'high',
          publishedAt: new Date(Date.now() - 30 * 60000).toISOString(),
        },
      ],
      important: [
        {
          id: '2',
          title: 'Tech Giants Report Strong Q4 Earnings',
          summary: 'Microsoft and Apple exceed analyst expectations with record revenue...',
          source: 'Financial Times',
          url: 'https://ft.com',
          sentiment: 'positive',
          tickers: ['MSFT', 'AAPL'],
          isBreaking: false,
          importance: 'high',
          publishedAt: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
        },
        {
          id: '3',
          title: 'Market Rally Continues Amid Positive Sentiment',
          summary: 'Global equity markets extend gains on optimistic economic outlook...',
          source: 'Bloomberg',
          url: 'https://bloomberg.com',
          sentiment: 'positive',
          tickers: ['VTI', 'VXUS'],
          isBreaking: false,
          importance: 'medium',
          publishedAt: new Date(Date.now() - 4 * 60 * 60000).toISOString(),
        },
        {
          id: '4',
          title: 'Oil Prices Decline on Demand Concerns',
          summary: 'Crude oil fell 2% amid recession fears in major economies...',
          source: 'MarketWatch',
          url: 'https://marketwatch.com',
          sentiment: 'negative',
          tickers: ['XLE', 'MPC'],
          isBreaking: false,
          importance: 'medium',
          publishedAt: new Date(Date.now() - 6 * 60 * 60000).toISOString(),
        },
      ],
    };

    return NextResponse.json(mockNews);
  } catch (error) {
    console.error('Error fetching news digest:', error);
    return NextResponse.json(
      { error: 'Failed to fetch news digest' },
      { status: 500 }
    );
  }
}
