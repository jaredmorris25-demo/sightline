'use client';

import dynamic from 'next/dynamic';

const SightingsMap = dynamic(() => import('./SightingsMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-screen flex items-center justify-center bg-gray-100">
      <p className="text-gray-400 text-sm">Loading map…</p>
    </div>
  ),
});

export default function HomeMap() {
  return <SightingsMap />;
}
