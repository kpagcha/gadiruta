/** Typed access to Gadiruta's direct-journey API without exposing provider payloads to React. */

import type { Place } from './places';

/** Enumerate the stable transport categories the journey API can expose. */
export type TransportMode = 'bus' | 'train' | 'tram' | 'boat' | 'metro' | 'unknown';

/** One normalized scheduled direct service returned by Gadiruta. */
export interface DirectJourney {
  line_code: string;
  transport_mode: TransportMode;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  note: string | null;
}

/** A complete direct-service search with the selected public places and upstream freshness time. */
export interface DirectJourneysResponse {
  origin: Place;
  destination: Place;
  date: string;
  depart_after: string | null;
  fetched_at: string;
  warnings: Array<'calendar_accuracy_not_guaranteed'>;
  items: DirectJourney[];
}

/** Identify a safe public API error without retaining untrusted backend message text. */
export class DirectJourneyRequestError extends Error {
  /** Preserve the HTTP status and stable API code for translated UI error handling. */
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super('Direct journey request failed.');
  }
}

/** Describe the URL-safe inputs Gadiruta accepts for one direct journey search. */
export interface DirectJourneySearchParameters {
  from: string;
  to: string;
  date: string;
  departAfter: string | null;
}

/** Narrow an untrusted JSON value to a non-null object. */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Validate the shared public place shape before using it in a journey result. */
function isPlace(value: unknown): value is Place {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value.id) &&
    typeof value.slug === 'string' &&
    /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value.slug) &&
    value.kind === 'population_centre' &&
    typeof value.name === 'string' &&
    value.name.trim().length > 0 &&
    (value.municipality === null || typeof value.municipality === 'string')
  );
}

/** Accept a strict API time string that can safely be shown without timezone conversion. */
function isTime(value: unknown): value is string {
  return typeof value === 'string' && /^(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$/.test(value);
}

/** Accept only the stable transport categories documented by Gadiruta's journey API. */
function isTransportMode(value: unknown): value is TransportMode {
  return (
    value === 'bus' ||
    value === 'train' ||
    value === 'tram' ||
    value === 'boat' ||
    value === 'metro' ||
    value === 'unknown'
  );
}

/** Validate one normalized service card and reject incomplete upstream translations. */
function isDirectJourney(value: unknown): value is DirectJourney {
  return (
    isRecord(value) &&
    typeof value.line_code === 'string' &&
    value.line_code.trim().length > 0 &&
    isTransportMode(value.transport_mode) &&
    isTime(value.departure_time) &&
    isTime(value.arrival_time) &&
    typeof value.duration_minutes === 'number' &&
    Number.isInteger(value.duration_minutes) &&
    value.duration_minutes >= 0 &&
    (value.note === null || typeof value.note === 'string')
  );
}

/** Validate the complete direct-journey response before it can update visible search state. */
function isDirectJourneysResponse(value: unknown): value is DirectJourneysResponse {
  return (
    isRecord(value) &&
    isPlace(value.origin) &&
    isPlace(value.destination) &&
    typeof value.date === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(value.date) &&
    (value.depart_after === null || isTime(value.depart_after)) &&
    typeof value.fetched_at === 'string' &&
    Number.isFinite(Date.parse(value.fetched_at)) &&
    Array.isArray(value.warnings) &&
    value.warnings.every((warning) => warning === 'calendar_accuracy_not_guaranteed') &&
    Array.isArray(value.items) &&
    value.items.every(isDirectJourney)
  );
}

/** Read the stable public error code if a failed API response supplies one. */
async function responseErrorCode(response: Response): Promise<string | null> {
  try {
    const payload: unknown = await response.json();
    return isRecord(payload) && typeof payload.code === 'string' ? payload.code : null;
  } catch {
    return null;
  }
}

/** Fetch one direct-service search with cancellation and the application's standard request timeout. */
export async function fetchDirectJourneys(
  parameters: DirectJourneySearchParameters,
  signal: AbortSignal,
): Promise<DirectJourneysResponse> {
  const query = new URLSearchParams({
    origin: parameters.from,
    destination: parameters.to,
    date: parameters.date,
  });
  if (parameters.departAfter) query.set('depart_after', parameters.departAfter);

  const response = await fetch(`/api/v1/journeys/direct?${query}`, {
    headers: { Accept: 'application/json' },
    signal: AbortSignal.any([signal, AbortSignal.timeout(25_000)]),
  });
  if (!response.ok) {
    throw new DirectJourneyRequestError(response.status, await responseErrorCode(response));
  }

  const payload: unknown = await response.json();
  if (!isDirectJourneysResponse(payload)) throw new Error('Invalid direct journey response.');
  return payload;
}
