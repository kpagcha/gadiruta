/** Retrieve one URL-defined direct journey search through the public Gadiruta API. */

import { useQuery } from '@tanstack/react-query';
import { fetchDirectJourneys, type DirectJourneySearchParameters } from '../../api/journeys';

/** Avoid requests for incomplete or malformed manually edited query strings. */
export function hasDirectJourneyParameters(
  parameters: DirectJourneySearchParameters | null,
): parameters is DirectJourneySearchParameters {
  return (
    parameters !== null &&
    /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(parameters.from) &&
    /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(parameters.to) &&
    parameters.from !== parameters.to &&
    /^\d{4}-\d{2}-\d{2}$/.test(parameters.date) &&
    (parameters.departAfter === null ||
      /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(parameters.departAfter))
  );
}

/** Cache one complete direct-service result while allowing explicit retry after upstream errors. */
export function useDirectJourneySearch(parameters: DirectJourneySearchParameters | null) {
  const enabled = hasDirectJourneyParameters(parameters);
  return useQuery({
    queryKey: [
      'direct-journeys',
      parameters?.from,
      parameters?.to,
      parameters?.date,
      parameters?.departAfter,
    ],
    queryFn: ({ signal }) => {
      if (!enabled) throw new Error('Direct journey search needs complete parameters.');
      return fetchDirectJourneys(parameters, signal);
    },
    enabled,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
    networkMode: 'always',
  });
}
