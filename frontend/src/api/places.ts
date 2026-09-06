/** Typed access to Gadiruta's public places API; never contact upstream providers from the browser. */

/** A selectable population centre using Gadiruta's opaque public identity. */
export interface Place {
  id: string;
  kind: 'population_centre';
  name: string;
  municipality: string | null;
}

/** Search results and the time their source catalogue was fetched. */
export interface PlacesResponse {
  items: Place[];
  fetched_at: string | null;
}

/** Narrow an untrusted JSON object without accepting arrays or null. */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Reject malformed suggestions before they enter the selection state. */
function isPlace(value: unknown): value is Place {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value.id) &&
    value.kind === 'population_centre' &&
    typeof value.name === 'string' &&
    value.name.trim().length > 0 &&
    (value.municipality === null || typeof value.municipality === 'string')
  );
}

/** Fetch a bounded suggestion list, allowing cancellation and a 25-second timeout.
 * Errors remain internal; the UI presents its own translated failure message.
 */
export async function fetchPlaces(query: string, signal: AbortSignal): Promise<PlacesResponse> {
  const parameters = new URLSearchParams({ q: query, limit: '8' });
  const response = await fetch(`/api/v1/places?${parameters}`, {
    headers: { Accept: 'application/json' },
    signal: AbortSignal.any([signal, AbortSignal.timeout(25_000)]),
  });
  if (!response.ok) throw new Error('Place search request failed.');

  const payload: unknown = await response.json();
  if (
    !isRecord(payload) ||
    !Array.isArray(payload.items) ||
    !payload.items.every(isPlace) ||
    !(
      payload.fetched_at === null ||
      (typeof payload.fetched_at === 'string' && Number.isFinite(Date.parse(payload.fetched_at)))
    )
  ) {
    throw new Error('Invalid place search response.');
  }
  return { items: payload.items, fetched_at: payload.fetched_at };
}
