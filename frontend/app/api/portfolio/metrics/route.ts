import { NextResponse } from 'next/server';
import type { PortfolioMetrics } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/portfolio/metrics
// Returns portfolio performance metrics
// ═══════════════════════════════════════════════════════════════════════════

export async function GET() {
  try {
    // TODO: Fetch from backend API or database
    // For now, return mock data
    const mockMetrics: PortfolioMetrics = {
      totalValue: 125000,
      dayChange: 2500,
      dayChangePercent: 2.04,
      weekChange: 5000,
      weekChangePercent: 4.17,
      monthChange: 12500,
      monthChangePercent: 11.11,
      averageScore: 72.5,
      topGainers: [],
      topLosers: [],
      diversificationScore: 78,
      riskScore: 45,
    };

    return NextResponse.json(mockMetrics);
  } catch (error) {
    console.error('Error fetching portfolio metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch portfolio metrics' },
      { status: 500 }
    );
  }
}
