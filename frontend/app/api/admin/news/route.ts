import { NextRequest, NextResponse } from 'next/server';

/**
 * Frontend API route to proxy news requests to the backend.
 * Proxies to: /news-admin/articles (backend)
 */

// Use the API URL environment variable or fall back to localhost
const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const ADMIN_KEY = process.env.ADMIN_API_KEY || process.env.NEXT_PUBLIC_ADMIN_KEY || 'marketgps-admin-2024';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    // Build query parameters for backend
    const backendParams = new URLSearchParams();

    if (searchParams.has('region')) {
      backendParams.append('source', searchParams.get('region')!);
    }
    if (searchParams.has('language')) {
      backendParams.append('language', searchParams.get('language')!);
    }
    if (searchParams.has('minViralityScore')) {
      backendParams.append('min_interactions', searchParams.get('minViralityScore')!);
    }
    if (searchParams.has('page')) {
      const page = parseInt(searchParams.get('page')!) || 1;
      const limit = parseInt(searchParams.get('limit')!) || 20;
      const offset = (page - 1) * limit;
      backendParams.append('offset', offset.toString());
      backendParams.append('limit', limit.toString());
    }
    if (searchParams.has('limit')) {
      backendParams.append('limit', searchParams.get('limit')!);
    }

    // Call backend
    const backendUrl = `${BACKEND_URL}/news-admin/articles?${backendParams.toString()}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'X-Admin-Key': ADMIN_KEY,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();

    // Transform backend response to match frontend expectations
    const articles = (data.articles || []).map((article: any) => ({
      id: article.id,
      title: article.title,
      source: article.source_name || article.source,
      region: article.country || 'Unknown',
      language: article.language || 'unknown',
      interactions: article.total_interactions || 0,
      viralityScore: calculateViralityScore(article.total_interactions || 0),
      publishedAt: article.published_at || article.scraped_at || new Date().toISOString(),
      hasScript: !!article.has_script,
      url: article.source_url || article.url,
      thumbnail: article.image_url || article.thumbnail_url,
    }));

    return NextResponse.json({
      articles,
      total: data.total || 0,
    });
  } catch (error) {
    console.error('Error fetching news:', error);
    return NextResponse.json(
      { error: 'Failed to fetch news' },
      { status: 500 }
    );
  }
}

/**
 * Calculate virality score based on interactions
 */
function calculateViralityScore(interactions: number): number {
  if (interactions >= 1000) return 5;
  if (interactions >= 500) return 4;
  if (interactions >= 250) return 3;
  if (interactions >= 100) return 2;
  if (interactions > 0) return 1;
  return 0;
}
