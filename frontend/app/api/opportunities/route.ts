import { NextResponse } from 'next/server';
import type { Opportunity } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/opportunities
// Returns detected opportunities
// ═══════════════════════════════════════════════════════════════════════════

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '5';

    // TODO: Fetch from backend API or database
    // For now, return mock data
    const mockOpportunities: Opportunity[] = [
      {
        asset: {
          asset_id: '1',
          ticker: 'VTI',
          symbol: 'VTI',
          name: 'Vanguard Total Stock Market ETF',
          asset_type: 'ETF',
          market_scope: 'US_EU',
          market_code: 'US',
          score_total: 85,
          score_value: 82,
          score_momentum: 88,
          score_safety: 78,
          coverage: 95,
          liquidity: 99,
          fx_risk: 0,
          updated_at: new Date().toISOString(),
        },
        type: 'high_score',
        scoreImprovement: 5,
        trend: 'up',
        confidence: 92,
        reason: 'Excellent diversification and consistent performance',
      },
      {
        asset: {
          asset_id: '2',
          ticker: 'MSFT',
          symbol: 'MSFT',
          name: 'Microsoft Corporation',
          asset_type: 'EQUITY',
          market_scope: 'US_EU',
          market_code: 'US',
          score_total: 78,
          score_value: 75,
          score_momentum: 82,
          score_safety: 76,
          coverage: 98,
          liquidity: 99,
          fx_risk: 0,
          updated_at: new Date().toISOString(),
        },
        type: 'trending',
        scoreImprovement: 3,
        trend: 'up',
        confidence: 85,
        reason: 'Strong upward momentum with positive news',
      },
      {
        asset: {
          asset_id: '3',
          ticker: 'VOO',
          symbol: 'VOO',
          name: 'Vanguard S&P 500 ETF',
          asset_type: 'ETF',
          market_scope: 'US_EU',
          market_code: 'US',
          score_total: 82,
          score_value: 80,
          score_momentum: 85,
          score_safety: 79,
          coverage: 96,
          liquidity: 99,
          fx_risk: 0,
          updated_at: new Date().toISOString(),
        },
        type: 'high_score',
        scoreImprovement: 4,
        trend: 'up',
        confidence: 88,
        reason: 'Stable performer with good risk-adjusted returns',
      },
    ];

    return NextResponse.json(mockOpportunities.slice(0, parseInt(limit)));
  } catch (error) {
    console.error('Error fetching opportunities:', error);
    return NextResponse.json(
      { error: 'Failed to fetch opportunities' },
      { status: 500 }
    );
  }
}
