import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

/**
 * Admin auth check endpoint.
 * Checks if the admin key stored in cookies is valid
 * by verifying it against the backend.
 */

function getBackendUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    'http://localhost:8000'
  );
}

export async function GET() {
  try {
    const cookieStore = await cookies();
    const adminKey = cookieStore.get('admin_key')?.value;

    if (!adminKey) {
      return NextResponse.json(
        { error: 'No admin key found' },
        { status: 401 }
      );
    }

    // Verify the key against the backend
    const backendUrl = getBackendUrl();
    const response = await fetch(`${backendUrl}/admin/auth/check`, {
      headers: {
        'X-Admin-Key': adminKey,
      },
      cache: 'no-store',
    });

    if (response.ok) {
      return NextResponse.json({ status: 'authorized', role: 'admin' });
    }

    return NextResponse.json(
      { error: 'Invalid admin key' },
      { status: 403 }
    );
  } catch (error) {
    console.error('Admin auth check failed:', error);
    return NextResponse.json(
      { error: 'Backend connection failed' },
      { status: 502 }
    );
  }
}
