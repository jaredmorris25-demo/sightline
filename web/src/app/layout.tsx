import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { auth0 } from '@/lib/auth0';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Sightline',
  description: 'Field observation platform for Australian wildlife, flora, and fungi',
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await auth0.getSession();

  // Provision the user in the Sightline database on first login.
  // get_or_create_user runs server-side inside the API — safe to call on every
  // layout render when a session exists; the API returns the existing record
  // on subsequent calls.
  if (session) {
    console.log('[layout] session detected, user:', session.user.email);
    try {
      const accessToken = session.tokenSet.accessToken;
      console.log('[layout] attempting POST /v1/users/me with token:', accessToken.slice(0, 20) + '…');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/users/me`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      });
      console.log('[layout] POST /v1/users/me →', res.status);
    } catch (err) {
      // Non-fatal — user provisioning failure should not break page render.
      console.error('[layout] POST /v1/users/me failed:', err);
    }
  } else {
    console.log('[layout] no session');
  }

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>
          <nav className="flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white">
            <a href="/" className="font-semibold text-green-800 tracking-tight">
              Sightline
            </a>
            <div className="flex items-center gap-6">
              <a href="/species" className="text-sm text-gray-600 hover:text-green-800">
                Species
              </a>
              {session ? (
                <a
                  href="/auth/logout"
                  className="text-sm px-4 py-1.5 rounded-full border border-gray-300 text-gray-700 hover:bg-gray-50"
                >
                  Logout
                </a>
              ) : (
                <a
                  href="/auth/login"
                  className="text-sm px-4 py-1.5 rounded-full bg-green-700 text-white hover:bg-green-800"
                >
                  Login
                </a>
              )}
            </div>
          </nav>
          {children}
        </Providers>
      </body>
    </html>
  );
}
