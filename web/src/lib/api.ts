import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// --- TypeScript interfaces matching API Pydantic schemas ---

export interface Species {
  id: string;
  common_name: string | null;
  scientific_name: string;
  kingdom: string | null;
  phylum: string | null;
  class_name: string | null;
  order_name: string | null;
  family: string | null;
  genus: string | null;
  inaturalist_id: string | null;
  gbif_id: string | null;
  ala_id: string | null;
  conservation_status: string | null;
  description: string | null;
  created_at: string;
}

export interface SpeciesSummary {
  id: string;
  common_name: string | null;
  scientific_name: string;
}

export interface UserPublic {
  id: string;
  display_name: string;
  avatar_url: string | null;
  role: 'observer' | 'curator' | 'admin';
}

export interface Sighting {
  id: string;
  user_id: string;
  species_id: string;
  group_id: string | null;
  observed_at: string;
  latitude: number;
  longitude: number;
  location_description: string | null;
  count: number | null;
  behaviour_notes: string | null;
  visibility: 'private' | 'group' | 'public';
  verified: boolean;
  verified_by: string | null;
  created_at: string;
}

export interface SightingDetail extends Sighting {
  species: SpeciesSummary | null;
  user: UserPublic | null;
}

export interface SightingCreate {
  species_id: string;
  observed_at: string;
  latitude: number;
  longitude: number;
  location_description?: string;
  count?: number;
  behaviour_notes?: string;
  visibility?: 'private' | 'group' | 'public';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// --- API functions ---

export const getSpecies = (params?: Record<string, unknown>) =>
  apiClient
    .get<PaginatedResponse<Species>>('/v1/species/', { params })
    .then((r) => r.data);

export const getSpeciesById = (id: string) =>
  apiClient.get<Species>(`/v1/species/${id}`).then((r) => r.data);

export const searchSpecies = (q: string) =>
  apiClient
    .get<SpeciesSummary[]>('/v1/species/search', { params: { q } })
    .then((r) => r.data);

export const getSightings = (params?: Record<string, unknown>) =>
  apiClient
    .get<PaginatedResponse<Sighting>>('/v1/sightings/', { params })
    .then((r) => r.data);

export const getSightingById = (id: string) =>
  apiClient.get<SightingDetail>(`/v1/sightings/${id}`).then((r) => r.data);

export const getNearbySightings = (lat: number, lng: number, radius_km = 50) =>
  apiClient
    .get<Sighting[]>('/v1/sightings/nearby', {
      params: { latitude: lat, longitude: lng, radius_km },
    })
    .then((r) => r.data);

export const createSighting = (payload: SightingCreate, token: string) =>
  apiClient
    .post<Sighting>('/v1/sightings/', payload, {
      headers: { Authorization: `Bearer ${token}` },
    })
    .then((r) => r.data);
