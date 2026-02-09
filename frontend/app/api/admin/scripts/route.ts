import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    // Build query parameters for backend
    const backendParams = new URLSearchParams();

    if (searchParams.has('status')) {
      backendParams.append('status', searchParams.get('status')!);
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

    // Call backend - try the viral-news endpoint first
    const backendUrl = `${BACKEND_URL}/api/viral-news/scripts?${backendParams.toString()}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();

    // Transform backend response to match frontend expectations
    const scripts = (data || []).map((script: any) => ({
      id: script.id,
      articleId: script.article_id,
      title: script.title,
      hook: script.hook,
      scriptText: script.script_text,
      wordCount: script.word_count,
      estimatedDuration: script.estimated_duration_seconds,
      status: script.status,
      createdAt: script.created_at,
      updatedAt: script.updated_at,
      articleTitle: script.articleTitle || script.article_title,
    }));

    return NextResponse.json({
      scripts,
      total: scripts.length,
    });
  } catch (error) {
    console.error('Error fetching scripts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scripts', scripts: [], total: 0 },
      { status: 200 } // Return 200 even on error to avoid breaking the app
    );
  }
}
