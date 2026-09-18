/** Render selected-place direct journey search, its shareable URL, and normalized result states. */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router';
import { DirectJourneyRequestError, type DirectJourneySearchParameters } from '../api/journeys';
import { Icon } from '../components/Icon';
import { PlaceAutocomplete } from '../features/journey-search/PlaceAutocomplete';
import type { PlaceFieldValue } from '../features/journey-search/PlaceAutocomplete';
import {
  hasDirectJourneyParameters,
  useDirectJourneySearch,
} from '../features/journey-search/useDirectJourneySearch';

/** Format the present calendar date in the backend's Europe/Madrid timezone for a date input. */
function madridToday(): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Madrid',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

/** Read complete query parameters without treating an arbitrary URL as a request until validation. */
function directJourneyParameters(
  searchParameters: URLSearchParams,
): DirectJourneySearchParameters | null {
  const from = searchParameters.get('from');
  const to = searchParameters.get('to');
  const date = searchParameters.get('date');
  if (!from || !to || !date) return null;
  const departAfter = searchParameters.get('depart_after');
  return { from, to, date, departAfter: departAfter || null };
}

/** Present an API clock time without converting a local timetable value through the browser timezone. */
function displayTime(value: string): string {
  return value.slice(0, 5);
}

/** Preserve both draft labels and confirmed identities while editing or swapping journey endpoints. */
export function HomePage() {
  const { t, i18n } = useTranslation();
  const [searchParameters, setSearchParameters] = useSearchParams();
  const submittedParameters = directJourneyParameters(searchParameters);
  const directSearch = useDirectJourneySearch(submittedParameters);
  const initialDate = submittedParameters?.date ?? madridToday();
  const [origin, setOrigin] = useState<PlaceFieldValue>({ text: '', place: null });
  const [destination, setDestination] = useState<PlaceFieldValue>({ text: '', place: null });
  const [journeyDate, setJourneyDate] = useState(initialDate);
  const [departAfter, setDepartAfter] = useState(submittedParameters?.departAfter ?? '');
  const [swapCount, setSwapCount] = useState(0);
  const displayedOrigin =
    origin.place || origin.text
      ? origin
      : directSearch.data
        ? { text: directSearch.data.origin.name, place: directSearch.data.origin }
        : origin;
  const displayedDestination =
    destination.place || destination.text
      ? destination
      : directSearch.data
        ? { text: directSearch.data.destination.name, place: directSearch.data.destination }
        : destination;
  const samePlace =
    displayedOrigin.place !== null && displayedOrigin.place.id === displayedDestination.place?.id;
  const canSubmit =
    displayedOrigin.place !== null && displayedDestination.place !== null && !samePlace;
  const currentYear = madridToday().slice(0, 4);

  /** Exchange complete field values, including partially typed input, in one React update. */
  function swapPlaces(): void {
    setOrigin(displayedDestination);
    setDestination(displayedOrigin);
    setSwapCount((count) => count + 1);
  }

  /** Write a new shareable URL only after both places have confirmed public identities. */
  function submitJourney(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!displayedOrigin.place || !displayedDestination.place || samePlace) return;
    const nextParameters = new URLSearchParams({
      from: displayedOrigin.place.slug,
      to: displayedDestination.place.slug,
      date: journeyDate,
    });
    if (departAfter) nextParameters.set('depart_after', departAfter);
    setSearchParameters(nextParameters);
  }

  /** Translate stable API errors without surfacing provider implementation details to the user. */
  function directSearchError(): string {
    if (!(directSearch.error instanceof DirectJourneyRequestError)) {
      return t('journey.resultsUnavailable');
    }
    if (directSearch.error.code === 'journey_place_not_found') {
      return t('journey.resultPlacesChanged');
    }
    if (directSearch.error.code === 'journey_date_unavailable') {
      return t('journey.resultDateUnavailable');
    }
    return t('journey.resultsUnavailable');
  }

  /** Format a duration using localized hour and minute fragments rather than timezone-aware dates. */
  function durationText(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (!hours) return t('journey.durationMinutes', { count: remainingMinutes });
    if (!remainingMinutes) return t('journey.durationHours', { count: hours });
    return t('journey.durationHoursMinutes', { hours, minutes: remainingMinutes });
  }

  const hasSubmittedSearch = hasDirectJourneyParameters(submittedParameters);
  const isSearching = hasSubmittedSearch && (directSearch.isPending || directSearch.isFetching);

  return (
    <main
      id="main-content"
      className="grid gap-10 py-12 min-[850px]:grid-cols-[1fr_1.12fr] min-[850px]:items-start min-[850px]:gap-16.25 min-[850px]:py-20 min-[850px]:pb-21.25"
      tabIndex={-1}
    >
      <div className="min-[850px]:pt-8.5">
        <p className="mb-5 text-xs font-[650] tracking-[1.8px] text-accent uppercase">
          {t('hero.eyebrow')}
        </p>
        <h1 className="text-[clamp(44px,7vw,76px)] leading-[1.05] font-[650] tracking-[-2.8px] whitespace-pre-line">
          {t('hero.title')}
        </h1>
        <p className="mt-6 max-w-92.5 text-[17px] leading-[1.65] text-muted max-[380px]:text-base">
          {t('hero.description')}
        </p>
        <p className="mt-8.5 flex items-center gap-3 text-[13px] text-muted">
          <span
            className="grid size-9.25 place-items-center rounded-full border border-line-brand text-accent"
            aria-hidden="true"
          >
            <Icon name="gadiruta" size={21} />
          </span>
          {t('hero.footnote')}
        </p>
      </div>

      <div className="grid min-w-0 gap-5">
        <section
          className="min-w-0 rounded-3xl border border-line bg-surface-card p-6 shadow-(--shadow-card) max-[380px]:p-4.5 min-[850px]:p-8"
          aria-labelledby="journey-title"
        >
          <div className="mb-7.5">
            <h2 id="journey-title" className="text-[23px] font-[650] tracking-[-0.6px]">
              {t('journey.title')}
            </h2>
            <p className="mt-2 text-sm leading-normal text-muted">{t('journey.description')}</p>
          </div>
          <form onSubmit={submitJourney}>
            <PlaceAutocomplete
              label={t('journey.origin')}
              placeholder={t('journey.originPlaceholder')}
              clearLabel={t('journey.clearOrigin')}
              value={displayedOrigin}
              onChange={setOrigin}
              endpoint="origin"
            />
            <div className="flex min-h-13.25 items-center justify-end gap-3">
              <span className="h-px flex-1 bg-line-subtle" aria-hidden="true" />
              <button
                type="button"
                className="grid size-11 place-items-center rounded-full border border-line bg-paper text-accent transition-colors hover:enabled:border-line-hover hover:enabled:bg-surface-hover-strong disabled:opacity-45"
                aria-label={t('journey.swap')}
                title={t('journey.swap')}
                disabled={!origin.text && !destination.text}
                onClick={swapPlaces}
              >
                <Icon name="swap" />
              </button>
            </div>
            <PlaceAutocomplete
              label={t('journey.destination')}
              placeholder={t('journey.destinationPlaceholder')}
              clearLabel={t('journey.clearDestination')}
              value={displayedDestination}
              onChange={setDestination}
              endpoint="destination"
            />

            <div className="mt-6.75 border-t border-line pt-5">
              <div className="grid gap-4 min-[540px]:grid-cols-2">
                <label className="grid gap-2 text-[13px] font-[650]" htmlFor="journey-date">
                  {t('journey.date')}
                  <input
                    id="journey-date"
                    className="min-h-12 rounded-xl border border-line-input bg-surface-input px-3 text-[15px] font-normal text-ink outline-none focus:border-accent"
                    type="date"
                    min={madridToday()}
                    max={`${currentYear}-12-31`}
                    required
                    value={journeyDate}
                    onChange={(event) => setJourneyDate(event.target.value)}
                  />
                </label>
                <label className="grid gap-2 text-[13px] font-[650]" htmlFor="journey-time">
                  {t('journey.time')}
                  <input
                    id="journey-time"
                    className="min-h-12 rounded-xl border border-line-input bg-surface-input px-3 text-[15px] font-normal text-ink outline-none focus:border-accent"
                    type="time"
                    value={departAfter}
                    onChange={(event) => setDepartAfter(event.target.value)}
                  />
                </label>
              </div>
              <p className="mt-2.5 text-xs leading-normal text-muted">{t('journey.dateHelp')}</p>
            </div>

            <div
              className="mt-5 min-h-15.25 border-t border-line pt-4.75"
              aria-live="polite"
              aria-atomic="true"
            >
              {samePlace ? (
                <p className="text-[13px] leading-normal text-warning">{t('journey.samePlace')}</p>
              ) : displayedOrigin.place && displayedDestination.place ? (
                <>
                  <p className="mb-2 text-[11px] tracking-[1px] text-muted uppercase">
                    {t('journey.selectionTitle')}
                  </p>
                  <p
                    className="flex flex-wrap items-center gap-2.25 text-base font-semibold wrap-anywhere"
                    aria-label={t('journey.selectionSummary', {
                      origin: displayedOrigin.place.name,
                      destination: displayedDestination.place.name,
                    })}
                  >
                    <span className="max-w-full">{displayedOrigin.place.name}</span>
                    <Icon name="arrow" className="size-5 shrink-0 text-icon-muted" />
                    <span className="max-w-full">{displayedDestination.place.name}</span>
                  </p>
                </>
              ) : (
                <p className="text-xs leading-normal text-muted">{t('journey.selectionHint')}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={!canSubmit}
              className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-[700] text-on-accent transition-opacity hover:enabled:opacity-90 disabled:opacity-45"
            >
              <Icon name="route" size={18} />
              {t('journey.submit')}
            </button>
          </form>
          <p className="sr-only" role="status" aria-live="polite">
            <span key={swapCount}>{swapCount > 0 ? t('journey.swapped') : ''}</span>
          </p>
        </section>

        {hasSubmittedSearch && (
          <section
            className="rounded-3xl border border-line bg-surface-card p-6 shadow-(--shadow-card) max-[380px]:p-4.5 min-[850px]:p-8"
            aria-labelledby="journey-results-title"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 id="journey-results-title" className="text-[21px] font-[650] tracking-[-0.5px]">
                  {t('journey.resultsTitle')}
                </h2>
                {directSearch.data && (
                  <p className="mt-1 text-sm text-muted">
                    {t('journey.resultsRoute', {
                      origin: directSearch.data.origin.name,
                      destination: directSearch.data.destination.name,
                    })}
                  </p>
                )}
              </div>
              {directSearch.data && (
                <p className="text-xs text-muted">
                  {t('journey.resultsFetchedAt', {
                    time: new Intl.DateTimeFormat(i18n.resolvedLanguage, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }).format(new Date(directSearch.data.fetched_at)),
                  })}
                </p>
              )}
            </div>

            {isSearching ? (
              <p
                className="mt-5 flex min-h-15 items-center gap-2.5 text-sm text-muted"
                role="status"
              >
                <Icon
                  name="loader"
                  className="size-4 shrink-0 animate-spin text-accent motion-reduce:animate-none"
                />
                {t('journey.resultsLoading')}
              </p>
            ) : directSearch.isError ? (
              <div className="mt-5 rounded-xl bg-paper px-4 py-4 text-sm leading-normal text-muted">
                <p>{directSearchError()}</p>
                <button
                  type="button"
                  className="mt-2 inline-flex min-h-11 items-center bg-transparent px-1.25 text-sm font-[650] text-accent underline decoration-1 underline-offset-4"
                  onClick={() => void directSearch.refetch()}
                >
                  {t('journey.resultsRetry')}
                </button>
              </div>
            ) : directSearch.data ? (
              <>
                <p className="mt-4 rounded-xl bg-paper px-4 py-3 text-xs leading-[1.6] text-muted">
                  {t('journey.calendarWarning')}
                </p>
                {directSearch.data.items.length ? (
                  <ol className="mt-4 grid list-none gap-3 p-0">
                    {directSearch.data.items.map((journey, index) => (
                      <li
                        key={`${journey.line_code}-${journey.departure_time}-${journey.arrival_time}-${index}`}
                        className="rounded-xl border border-line-subtle bg-surface-input px-4 py-4"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                          <span className="rounded-md bg-surface-active px-2 py-1 text-xs font-[700] text-accent">
                            {t('journey.line', { line: journey.line_code })}
                          </span>
                          <span className="text-xs text-muted">
                            {durationText(journey.duration_minutes)}
                          </span>
                        </div>
                        <div className="mt-3 flex items-center gap-3 tabular-nums">
                          <time className="text-[25px] font-[700] tracking-[-0.8px]">
                            {displayTime(journey.departure_time)}
                          </time>
                          <Icon name="arrow" className="size-5 shrink-0 text-icon-muted" />
                          <time className="text-[25px] font-[700] tracking-[-0.8px]">
                            {displayTime(journey.arrival_time)}
                          </time>
                        </div>
                        {journey.note && (
                          <p className="mt-2.5 text-xs leading-[1.55] text-muted">{journey.note}</p>
                        )}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="mt-5 rounded-xl bg-paper px-4 py-4 text-sm leading-[1.6] text-muted">
                    {t('journey.resultsEmpty')}
                  </p>
                )}
              </>
            ) : null}
          </section>
        )}
      </div>
    </main>
  );
}
