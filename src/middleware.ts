import { NextResponse } from 'next/server';
import { authMiddleware } from '@clerk/nextjs';

export default authMiddleware({
  publicRoutes: [
    '/',
    '/sign-in(.*)',
    '/sign-up(.*)',
    '/pricing(.*)',
    '/api/webhooks/clerk',
    '/api/stripe/webhook',
  ],
  signInUrl: '/sign-in',
  afterAuth(auth, req) {
    const { userId } = auth;
    const url = req.nextUrl;
    // Redirect signed-in users away from auth/public entry pages
    if (userId) {
      const path = url.pathname;
      if (path === '/' || path.startsWith('/sign-in') || path.startsWith('/sign-up')) {
        return NextResponse.redirect(new URL('/dashboard', req.url));
      }
    }

    // Continue and add headers; rely on Clerk's default redirect for private routes
    const res = NextResponse.next();
    const isProduction = process.env.NODE_ENV === 'production';
    const hostname = req.headers.get('host') || '';
    if (!isProduction || hostname.includes('localhost')) {
      res.headers.set('X-Robots-Tag', 'noindex, nofollow');
    }
    res.headers.set('X-Frame-Options', 'DENY');
    res.headers.set('X-Content-Type-Options', 'nosniff');
    res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    return res;
  },
});

// Apply middleware to all routes including API routes, but excluding static assets
export const config = {
  matcher: [
    // Match all paths except static files and _next
    '/((?!.+\\.[\\w]+$|_next).*)',
    // Match root path
    '/',
    // Match all API and trpc routes
    '/(api|trpc)(.*)',
  ],
};
