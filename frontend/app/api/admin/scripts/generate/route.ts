import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { articleId } = body;

    if (!articleId) {
      return NextResponse.json(
        { error: 'articleId is required' },
        { status: 400 }
      );
    }

    // Call backend to generate script
    const response = await fetch(`${BACKEND_URL}/api/viral-news/generate-script`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        article_id: articleId,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Backend error: ${response.status} - ${error}`);
    }

    const data = await response.json();

    return NextResponse.json({
      success: true,
      script: data,
    });
  } catch (error) {
    console.error('Error generating script:', error);
    return NextResponse.json(
      { error: 'Failed to generate script' },
      { status: 500 }
    );
  }
}
