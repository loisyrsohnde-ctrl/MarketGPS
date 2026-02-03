import { NextResponse } from 'next/server';
import type { Alert } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/alerts
// Returns recent alerts with unread count
// ═══════════════════════════════════════════════════════════════════════════

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '3';

    // TODO: Fetch from backend API or database
    // For now, return mock data
    const mockAlerts: Alert[] = [
      {
        id: '1',
        type: 'score',
        severity: 'high',
        title: 'Score Surge Detected',
        message: 'AAPL score increased by 8 points',
        ticker: 'AAPL',
        isRead: false,
        createdAt: new Date(Date.now() - 15 * 60000).toISOString(),
        metadata: {
          oldValue: 72,
          newValue: 80,
          change: 8,
          changePercent: 11.1,
        },
      },
      {
        id: '2',
        type: 'price',
        severity: 'medium',
        title: 'Price Target Hit',
        message: 'TSLA reached your price alert target',
        ticker: 'TSLA',
        isRead: false,
        createdAt: new Date(Date.now() - 45 * 60000).toISOString(),
      },
      {
        id: '3',
        type: 'news',
        severity: 'low',
        title: 'News Update',
        message: 'New coverage on MSFT',
        ticker: 'MSFT',
        isRead: true,
        createdAt: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
      },
    ];

    return NextResponse.json({
      unreadCount: 2,
      criticalCount: 0,
      recent: mockAlerts.slice(0, parseInt(limit)),
    });
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts' },
      { status: 500 }
    );
  }
}
