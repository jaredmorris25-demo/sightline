'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { searchSpecies, type SpeciesSummary, type SightingCreate } from '@/lib/api';

function toLocalDatetimeValue(d: Date): string {
  // Returns a string suitable for datetime-local input: "YYYY-MM-DDTHH:mm"
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    d.getFullYear() +
    '-' + pad(d.getMonth() + 1) +
    '-' + pad(d.getDate()) +
    'T' + pad(d.getHours()) +
    ':' + pad(d.getMinutes())
  );
}

interface Props {
  accessToken: string;
}

export default function SubmitSightingForm({ accessToken }: Props) {
  const router = useRouter();

  // Species search
  const [speciesQuery, setSpeciesQuery] = useState('');
  const [speciesResults, setSpeciesResults] = useState<SpeciesSummary[]>([]);
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesSummary | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Form fields
  const [observedAt, setObservedAt] = useState(() => toLocalDatetimeValue(new Date()));
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [count, setCount] = useState('1');
  const [behaviourNotes, setBehaviourNotes] = useState('');
  const [visibility, setVisibility] = useState<'public' | 'group' | 'private'>('public');
  const [locationDescription, setLocationDescription] = useState('');

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pre-populate lat/lng from browser Geolocation
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setLatitude(pos.coords.latitude.toFixed(6));
        setLongitude(pos.coords.longitude.toFixed(6));
      });
    }
  }, []);

  // Debounced species search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (speciesQuery.length < 2) {
      setSpeciesResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchSpecies(speciesQuery);
        setSpeciesResults(results);
        setShowDropdown(results.length > 0);
      } catch {
        setSpeciesResults([]);
      }
    }, 300);
  }, [speciesQuery]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!selectedSpecies) {
      setError('Please select a species from the search results.');
      return;
    }

    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lng)) {
      setError('Latitude and longitude are required.');
      return;
    }

    // Convert local datetime string to ISO 8601 with UTC offset
    const observedDate = new Date(observedAt);
    if (observedDate > new Date()) {
      setError('Observed at cannot be in the future.');
      return;
    }

    const payload: SightingCreate = {
      species_id: selectedSpecies.id,
      observed_at: observedDate.toISOString(),
      latitude: lat,
      longitude: lng,
      count: count ? parseInt(count, 10) : 1,
      behaviour_notes: behaviourNotes || undefined,
      visibility,
      location_description: locationDescription || undefined,
    };

    setSubmitting(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/sightings/`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? `Server returned ${res.status}`);
      }

      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">

      {/* Species search */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Species <span className="text-red-500">*</span>
        </label>
        {selectedSpecies ? (
          <div className="flex items-center justify-between px-4 py-2 border border-green-500 rounded-lg bg-green-50">
            <div>
              <span className="text-sm font-medium text-gray-900">
                {selectedSpecies.common_name ?? selectedSpecies.scientific_name}
              </span>
              <span className="text-xs text-gray-500 italic ml-2">
                {selectedSpecies.scientific_name}
              </span>
            </div>
            <button
              type="button"
              onClick={() => { setSelectedSpecies(null); setSpeciesQuery(''); }}
              className="text-xs text-gray-400 hover:text-gray-600 ml-4"
            >
              Change
            </button>
          </div>
        ) : (
          <>
            <input
              type="search"
              placeholder="Search species by name…"
              value={speciesQuery}
              onChange={(e) => setSpeciesQuery(e.target.value)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
            />
            {showDropdown && (
              <ul className="absolute z-20 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-52 overflow-y-auto">
                {speciesResults.map((s) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      onMouseDown={() => {
                        setSelectedSpecies(s);
                        setSpeciesQuery('');
                        setShowDropdown(false);
                      }}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
                    >
                      <span className="font-medium text-gray-900">
                        {s.common_name ?? s.scientific_name}
                      </span>
                      <span className="text-gray-400 italic ml-2 text-xs">
                        {s.scientific_name}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      {/* Observed at */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Observed at <span className="text-red-500">*</span>
        </label>
        <input
          type="datetime-local"
          value={observedAt}
          max={toLocalDatetimeValue(new Date())}
          onChange={(e) => setObservedAt(e.target.value)}
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
        />
      </div>

      {/* Lat / Lng */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Latitude <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            required
            placeholder="-33.8688"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Longitude <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            required
            placeholder="151.2093"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
          />
        </div>
      </div>

      {/* Count */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Count</label>
        <input
          type="number"
          min="1"
          value={count}
          onChange={(e) => setCount(e.target.value)}
          className="w-40 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
        />
      </div>

      {/* Location description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Location description
        </label>
        <input
          type="text"
          value={locationDescription}
          onChange={(e) => setLocationDescription(e.target.value)}
          placeholder="e.g. Near the creek, southern bank"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
        />
      </div>

      {/* Behaviour notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Behaviour notes
        </label>
        <textarea
          value={behaviourNotes}
          onChange={(e) => setBehaviourNotes(e.target.value)}
          rows={3}
          placeholder="What was the animal doing?"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600 resize-none"
        />
      </div>

      {/* Visibility */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Visibility</label>
        <select
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as 'public' | 'group' | 'private')}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
        >
          <option value="public">Public</option>
          <option value="group">Group</option>
          <option value="private">Private</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={submitting}
        className="px-6 py-2.5 bg-green-700 text-white text-sm font-medium rounded-full hover:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? 'Submitting…' : 'Submit sighting'}
      </button>
    </form>
  );
}
