'use client';

import { useState } from 'react';
import Map, { Marker, Popup } from 'react-map-gl/mapbox';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import 'mapbox-gl/dist/mapbox-gl.css';
import { getSightings, type Sighting } from '@/lib/api';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

export default function SightingsMap() {
  const [selected, setSelected] = useState<Sighting | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['sightings', 'map'],
    queryFn: () => getSightings({ limit: 100 }),
  });

  if (!MAPBOX_TOKEN) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gray-100">
        <p className="text-gray-500 text-sm">
          Map unavailable — set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local
        </p>
      </div>
    );
  }

  return (
    <Map
      initialViewState={{ longitude: 133.7751, latitude: -25.2744, zoom: 4 }}
      style={{ width: '100%', height: '100vh' }}
      mapStyle="mapbox://styles/mapbox/outdoors-v12"
      mapboxAccessToken={MAPBOX_TOKEN}
    >
      {!isLoading &&
        data?.items.map((sighting) => (
          <Marker
            key={sighting.id}
            longitude={sighting.longitude}
            latitude={sighting.latitude}
            color="#16a34a"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setSelected(sighting);
            }}
          />
        ))}

      {selected && (
        <Popup
          longitude={selected.longitude}
          latitude={selected.latitude}
          onClose={() => setSelected(null)}
          closeButton
          closeOnClick={false}
          anchor="bottom"
        >
          <div className="text-sm p-1 space-y-1">
            <p className="text-gray-500">
              {new Date(selected.observed_at).toLocaleDateString('en-AU', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}
            </p>
            <Link
              href={`/sightings/${selected.id}`}
              className="text-green-700 font-medium hover:underline block"
            >
              View sighting →
            </Link>
          </div>
        </Popup>
      )}
    </Map>
  );
}
