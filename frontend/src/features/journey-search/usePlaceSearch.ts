/** Debounce and cache place suggestions independently of field selection state. */
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { fetchPlaces } from '../../api/places';

/** Avoid searches containing only whitespace or a single accent-folded character. */
export function canSearchPlaces(text: string): boolean {
  return Array.from(text.trim().normalize('NFKD').replace(/\p{M}/gu, '')).length >= 2;
}

/** Share results between fields while keeping stale queries out of the current suggestion list. */
export function usePlaceSearch(text: string, enabled: boolean) {
  const query = text.trim();
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const isDebouncing = query !== debouncedQuery;
  const result = useQuery({
    queryKey: ['places', query],
    queryFn: ({ signal }) => fetchPlaces(query, signal),
    enabled: enabled && canSearchPlaces(query) && !isDebouncing,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
    networkMode: 'always',
  });

  return { ...result, isDebouncing };
}
