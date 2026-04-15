import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getSpeciesById, getSightings, type Sighting } from '@/lib/api';

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SpeciesDetailPage({ params }: Props) {
  const { id } = await params;

  const [species, sightingsPage] = await Promise.all([
    getSpeciesById(id).catch(() => null),
    getSightings({ species_id: id, limit: 10 }).catch(() => null),
  ]);

  if (!species) notFound();

  const taxonomy: [string, string | null][] = [
    ['Kingdom', species.kingdom],
    ['Phylum', species.phylum],
    ['Class', species.class_name],
    ['Order', species.order_name],
    ['Family', species.family],
    ['Genus', species.genus],
  ];

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <Link href="/species" className="text-sm text-green-700 hover:underline mb-6 block">
        ← Species
      </Link>

      <h1 className="text-3xl font-semibold text-gray-900">
        {species.common_name ?? species.scientific_name}
      </h1>
      <p className="text-lg text-gray-500 italic mt-1">{species.scientific_name}</p>

      {species.conservation_status && (
        <span className="inline-block mt-3 px-3 py-1 text-xs font-medium bg-amber-100 text-amber-800 rounded-full">
          IUCN: {species.conservation_status}
        </span>
      )}

      {species.description && (
        <p className="mt-4 text-gray-700 leading-relaxed">{species.description}</p>
      )}

      <section className="mt-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Taxonomy
        </h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2">
          {taxonomy.map(
            ([label, value]) =>
              value && (
                <div key={label} className="flex gap-2 text-sm">
                  <dt className="text-gray-400 w-16 shrink-0">{label}</dt>
                  <dd className="text-gray-800">{value}</dd>
                </div>
              )
          )}
        </dl>
      </section>

      {sightingsPage && sightingsPage.items.length > 0 && (
        <section className="mt-10">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Recent sightings
          </h2>
          <ul className="space-y-2">
            {sightingsPage.items.map((s: Sighting) => (
              <li key={s.id}>
                <Link
                  href={`/sightings/${s.id}`}
                  className="flex items-center justify-between text-sm px-4 py-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
                >
                  <span className="text-gray-700">
                    {new Date(s.observed_at).toLocaleDateString('en-AU', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </span>
                  <span className="text-gray-400 text-xs">
                    {s.latitude.toFixed(3)}, {s.longitude.toFixed(3)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
