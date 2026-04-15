import { auth0 } from '@/lib/auth0';
import HomeMap from '@/components/HomeMap';

export default async function HomePage() {
  const session = await auth0.getSession();

  return (
    <div className="relative w-full h-[calc(100vh-49px)]">
      {/* Floating login/logout button overlaid on the map */}
      <div className="absolute top-4 right-4 z-10">
        {session ? (
          <a
            href="/auth/logout"
            className="text-sm px-4 py-2 rounded-full bg-white/90 backdrop-blur-sm border border-gray-200 text-gray-700 hover:bg-white shadow-sm"
          >
            Logout
          </a>
        ) : (
          <a
            href="/auth/login"
            className="text-sm px-4 py-2 rounded-full bg-green-700 text-white hover:bg-green-800 shadow-sm"
          >
            Login
          </a>
        )}
      </div>

      <HomeMap />
    </div>
  );
}
