import { NextResponse } from 'next/server';
import { authMiddleware } from '@clerk/nextjs';

export default authMiddleware({
  publicRoutes: [
    '/',
    '/sign-in(.*)',
    '/sign-up(.*)',
    '/pricing(.*)',
    '/legal(.*)'
  ],
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
    const isProduction = process.env.NEXT_PUBLIC_ENV === 'production';
    const hostname = req.headers.get('host') || '';
    if (!isProduction || hostname.includes('localhost') || hostname.includes('.vercel.app')) {
      res.headers.set('X-Robots-Tag', 'noindex, nofollow');
    }
    res.headers.set('X-Frame-Options', 'DENY');
    res.headers.set('X-Content-Type-Options', 'nosniff');
    res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    return res;
  },
});

// Apply middleware to all routes except static assets, public files, and API routes
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|txt|xml)$).*)',
  ],
};

