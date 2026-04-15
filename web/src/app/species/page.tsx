'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { getSpecies, searchSpecies, type Species, type SpeciesSummary } from '@/lib/api';

const LIMIT = 20;

export default function SpeciesPage() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [page, setPage] = useState(0);

  // 300ms debounce on the search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const isSearching = debouncedQuery.length >= 2;

  const { data: searchResults, isFetching: searchFetching } = useQuery({
    queryKey: ['species-search', debouncedQuery],
    queryFn: () => searchSpecies(debouncedQuery),
    enabled: isSearching,
  });

  const { data: pagedResults, isFetching: pageFetching } = useQuery({
    queryKey: ['species-list', page],
    queryFn: () => getSpecies({ skip: page * LIMIT, limit: LIMIT }),
    enabled: !isSearching,
  });

  const isLoading = isSearching ? searchFetching : pageFetching;
  const totalPages = pagedResults ? Math.ceil(pagedResults.total / LIMIT) : 0;

  // Normalise both result shapes to a common card type
  type CardSpecies = Pick<Species, 'id' | 'common_name' | 'scientific_name' | 'kingdom' | 'family'>;
  const cards: CardSpecies[] = isSearching
    ? (searchResults ?? []).map((s: SpeciesSummary) => ({
        id: s.id,
        common_name: s.common_name,
        scientific_name: s.scientific_name,
        kingdom: null,
        family: null,
      }))
    : (pagedResults?.items ?? []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-semibold text-gray-900 mb-6">Species</h1>

      <input
        type="search"
        placeholder="Search species…"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setPage(0);
        }}
        className="w-full max-w-md mb-8 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
      />

      {isLoading && (
        <p className="text-gray-400 text-sm mb-4">Loading…</p>
      )}

      {!isLoading && cards.length === 0 && (
        <p className="text-gray-500 text-sm">No species found.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {cards.map((s) => (
          <Link
            key={s.id}
            href={`/species/${s.id}`}
            className="block p-4 bg-white border border-gray-200 rounded-xl hover:shadow-md transition-shadow"
          >
            <p className="font-medium text-gray-900 text-sm leading-snug">
              {s.common_name ?? s.scientific_name}
            </p>
            <p className="text-xs text-gray-500 italic mt-1">{s.scientific_name}</p>
            {(s.kingdom || s.family) && (
              <p className="text-xs text-gray-400 mt-2">
                {[s.kingdom, s.family].filter(Boolean).join(' · ')}
              </p>
            )}
          </Link>
        ))}
      </div>

      {!isSearching && totalPages > 1 && (
        <div className="flex items-center gap-4 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
