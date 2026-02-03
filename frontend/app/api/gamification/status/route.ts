import { NextResponse } from 'next/server';
import type { GamificationStatus } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/gamification/status
// Returns current gamification status
// ═══════════════════════════════════════════════════════════════════════════

export async function GET() {
  try {
    // TODO: Fetch from backend API or database
    // For now, return mock data
    const mockStatus: GamificationStatus = {
      level: 'analyst',
      points: 4250,
      weeklyPoints: 420,
      weeklyTarget: 500,
      objectives: [
        {
          id: '1',
          title: 'Add 5 Assets to Watchlist',
          description: 'Expand your watchlist with 5 new assets',
          progress: 3,
          target: 5,
          category: 'engagement',
          reward: 100,
          isCompleted: false,
          dueDate: new Date(Date.now() + 4 * 24 * 60 * 60000).toISOString(),
        },
        {
          id: '2',
          title: 'Review Market News Daily',
          description: 'Read market news every day this week',
          progress: 5,
          target: 7,
          category: 'learning',
          reward: 50,
          isCompleted: false,
          dueDate: new Date(Date.now() + 2 * 24 * 60 * 60000).toISOString(),
        },
        {
          id: '3',
          title: 'Diversify Your Portfolio',
          description: 'Achieve at least 5 different asset types',
          progress: 4,
          target: 5,
          category: 'portfolio',
          reward: 150,
          isCompleted: false,
          dueDate: new Date(Date.now() + 3 * 24 * 60 * 60000).toISOString(),
        },
      ],
      streakDays: 7,
    };

    return NextResponse.json(mockStatus);
  } catch (error) {
    console.error('Error fetching gamification status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch gamification status' },
      { status: 500 }
    );
  }
}
