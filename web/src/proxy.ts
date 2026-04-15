/**
 * Auth0 proxy for Next.js 16.
 * Handles /auth/login, /auth/callback, /auth/logout, and rolling sessions.
 * In Next.js 16, proxy.ts replaces middleware.ts for the Node runtime.
 */
import { auth0 } from '@/lib/auth0';

export async function proxy(request: Request) {
  return await auth0.middleware(request);
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)',
  ],
};
