import { NextResponse } from 'next/server';

// ═══════════════════════════════════════════════════════════════════════════
// POST /api/watchlist
// Adds an asset to the user's watchlist
// ═══════════════════════════════════════════════════════════════════════════

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { ticker, notes } = body;

    if (!ticker) {
      return NextResponse.json(
        { error: 'Ticker is required' },
        { status: 400 }
      );
    }

    // TODO: Save to backend API or database
    // For now, just return success
    return NextResponse.json({
      success: true,
      message: `Added ${ticker} to watchlist`,
      data: {
        ticker,
        notes,
        addedAt: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error('Error adding to watchlist:', error);
    return NextResponse.json(
      { error: 'Failed to add to watchlist' },
      { status: 500 }
    );
  }
}
