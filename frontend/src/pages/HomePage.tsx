/** Render selected-place direct journey search, its shareable URL, and normalized result states. */

import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router';
import { DirectJourneyRequestError, type DirectJourneySearchParameters } from '../api/journeys';
import { Icon } from '../components/Icon';
import { JourneyDateTimePicker } from '../features/journey-search/JourneyDateTimePicker';
import { PlaceAutocomplete } from '../features/journey-search/PlaceAutocomplete';
import type { PlaceFieldValue } from '../features/journey-search/PlaceAutocomplete';
import {
  hasDirectJourneyParameters,
  useDirectJourneySearch,
} from '../features/journey-search/useDirectJourneySearch';

const VISIBLE_JOURNEY_COUNT = 4;
const APPROXIMATE_SCHEDULE_DAYS = 60;

/** Track how many services from one fetched result should be visible. */
interface JourneyResultPage {
  fetchedAt: string;
  page: number;
}

/** Format the present calendar date in the backend's Europe/Madrid timezone. */
function madridToday(): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Madrid',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return values.year + '-' + values.month + '-' + values.day;
}

/** Read a complete direct-search URL only when it has every required parameter. */
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

/** Present an API clock time without converting a local timetable through the browser timezone. */
function displayTime(value: string): string {
  return value.slice(0, 5);
}

/** Convert an ISO calendar date to a timezone-independent timestamp. */
function calendarTimestamp(value: string): number {
  const [year = 0, month = 1, day = 1] = value.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
}

/** Flag dates far enough ahead that operators may still change their timetables. */
function isScheduleApproximate(date: string, today: string): boolean {
  return (
    calendarTimestamp(date) - calendarTimestamp(today) >= APPROXIMATE_SCHEDULE_DAYS * 86_400_000
  );
}

/** Render the home search form and direct-service results. */
export function HomePage() {
  const { t } = useTranslation();
  const [searchParameters, setSearchParameters] = useSearchParams();
  const submittedParameters = directJourneyParameters(searchParameters);
  const directSearch = useDirectJourneySearch(submittedParameters);
  const today = madridToday();
  const [origin, setOrigin] = useState<PlaceFieldValue>({ text: '', place: null });
  const [destination, setDestination] = useState<PlaceFieldValue>({ text: '', place: null });
  const [journeyDate, setJourneyDate] = useState(submittedParameters?.date ?? today);
  const [departAfter, setDepartAfter] = useState(submittedParameters?.departAfter ?? '');
  const [swapCount, setSwapCount] = useState(0);
  const [expandedSearchKey, setExpandedSearchKey] = useState<string | null>(null);
  const [journeyResultPage, setJourneyResultPage] = useState<JourneyResultPage | null>(null);
  const hydratedSearchRef = useRef<string | null>(null);
  const maximumDate = today.slice(0, 4) + '-12-31';
  const samePlace = origin.place !== null && origin.place.id === destination.place?.id;
  const canSubmit = origin.place !== null && destination.place !== null && !samePlace;
  const hasSubmittedSearch = hasDirectJourneyParameters(submittedParameters);
  const submittedSearchKey = submittedParameters
    ? [
        submittedParameters.from,
        submittedParameters.to,
        submittedParameters.date,
        submittedParameters.departAfter ?? '',
      ].join(':')
    : null;
  const isSearching = hasSubmittedSearch && (directSearch.isPending || directSearch.isFetching);
  const hasDirectServices = Boolean(directSearch.data?.items.length);
  const showCompactSearch = hasDirectServices && expandedSearchKey !== submittedSearchKey;
  const schedulesAreApproximate = isScheduleApproximate(journeyDate, today);
  const currentJourneyPage =
    journeyResultPage !== null && journeyResultPage.fetchedAt === directSearch.data?.fetched_at
      ? journeyResultPage.page
      : 1;
  const visibleJourneyCount = currentJourneyPage * VISIBLE_JOURNEY_COUNT;
  const visibleJourneys = directSearch.data
    ? directSearch.data.items.slice(0, visibleJourneyCount)
    : [];

  useEffect(() => {
    if (!directSearch.data || !submittedParameters) return;
    const searchKey = [
      submittedParameters.from,
      submittedParameters.to,
      submittedParameters.date,
      submittedParameters.departAfter ?? '',
    ].join(':');
    if (hydratedSearchRef.current === searchKey) return;
    setOrigin((current) =>
      current.text || current.place
        ? current
        : { text: directSearch.data.origin.name, place: directSearch.data.origin },
    );
    setDestination((current) =>
      current.text || current.place
        ? current
        : { text: directSearch.data.destination.name, place: directSearch.data.destination },
    );
    hydratedSearchRef.current = searchKey;
  }, [directSearch.data, submittedParameters]);

  /** Exchange complete field values, including partially typed input, in one React update. */
  function swapPlaces(): void {
    setOrigin(destination);
    setDestination(origin);
    setSwapCount((count) => count + 1);
    if (destination.place && origin.place) searchJourneys(destination, origin);
  }

  /** Start a new URL-defined search or refresh the current one when its parameters are unchanged. */
  function searchJourneys(nextOrigin: PlaceFieldValue, nextDestination: PlaceFieldValue): void {
    if (
      !nextOrigin.place ||
      !nextDestination.place ||
      nextOrigin.place.id === nextDestination.place.id
    ) {
      return;
    }
    const nextParameters = new URLSearchParams({
      from: nextOrigin.place.slug,
      to: nextDestination.place.slug,
      date: journeyDate,
    });
    if (departAfter) nextParameters.set('depart_after', departAfter);
    const isCurrentSearch =
      submittedParameters?.from === nextOrigin.place.slug &&
      submittedParameters.to === nextDestination.place.slug &&
      submittedParameters.date === journeyDate &&
      submittedParameters.departAfter === (departAfter || null);
    if (isCurrentSearch) {
      void directSearch.refetch();
      return;
    }
    setSearchParameters(nextParameters);
  }

  /** Update the origin and automatically search once the destination is already confirmed. */
  function updateOrigin(nextOrigin: PlaceFieldValue): void {
    setOrigin(nextOrigin);
    if (nextOrigin.place && destination.place) searchJourneys(nextOrigin, destination);
  }

  /** Update the destination and automatically search once the origin is already confirmed. */
  function updateDestination(nextDestination: PlaceFieldValue): void {
    setDestination(nextDestination);
    if (origin.place && nextDestination.place) searchJourneys(origin, nextDestination);
  }

  /** Allow the button to refresh the current search in addition to submitting a changed route. */
  function submitJourney(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    searchJourneys(origin, destination);
  }

  /** Translate stable API errors without exposing provider implementation details. */
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

  /** Format a duration using localized hour and minute fragments. */
  function durationText(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (!hours) return t('journey.durationMinutes', { count: remainingMinutes });
    if (!remainingMinutes) return t('journey.durationHours', { count: hours });
    return t('journey.durationHoursMinutes', { hours, minutes: remainingMinutes });
  }

  const pageLayout = hasSubmittedSearch
    ? 'min-[850px]:grid-cols-[0.86fr_1.14fr]'
    : 'min-[850px]:grid-cols-[1fr_1.12fr]';
  const searchPanelClass =
    'min-w-0 rounded-3xl border border-line bg-surface-card p-6 shadow-(--shadow-card) max-[380px]:p-4.5 min-[850px]:p-8 ' +
    (hasSubmittedSearch ? 'journey-panel-enter' : '');

  return (
    <main
      id="main-content"
      className={
        'grid gap-10 py-12 min-[850px]:items-start min-[850px]:gap-16.25 min-[850px]:py-20 min-[850px]:pb-21.25 ' +
        pageLayout
      }
      tabIndex={-1}
    >
      {!hasSubmittedSearch && (
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
      )}

      <section className={searchPanelClass} aria-label={t('journey.searchForm')}>
        {showCompactSearch && origin.place && destination.place && (
          <div className="min-[850px]:hidden">
            <button
              type="button"
              className="grid w-full gap-3 rounded-2xl bg-surface-input p-3 text-left"
              aria-label={t('journey.selectionSummary', {
                origin: origin.place.name,
                destination: destination.place.name,
              })}
              onClick={() => setExpandedSearchKey(submittedSearchKey)}
            >
              <span className="flex min-w-0 items-center gap-2 text-sm font-[700] wrap-anywhere">
                <span className="min-w-0 truncate">{origin.place.name}</span>
                <Icon name="arrow" className="size-4 shrink-0 text-icon-muted" />
                <span className="min-w-0 truncate">{destination.place.name}</span>
              </span>
              <span className="text-xs font-[650] text-accent">{t('journey.changeSearch')}</span>
            </button>
            {schedulesAreApproximate && (
              <p className="mt-3 text-xs leading-[1.55] text-muted">
                {t('journey.scheduleApproximation')}
              </p>
            )}
          </div>
        )}

        <div className={showCompactSearch ? 'hidden min-[850px]:block' : ''}>
          <form onSubmit={submitJourney}>
            <PlaceAutocomplete
              label={t('journey.origin')}
              placeholder={t('journey.originPlaceholder')}
              clearLabel={t('journey.clearOrigin')}
              value={origin}
              onChange={updateOrigin}
              endpoint="origin"
            />
            <div className="flex min-h-[79px] items-start justify-end gap-3 pt-8">
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
              value={destination}
              onChange={updateDestination}
              endpoint="destination"
            />

            <div className="mt-6.75 border-t border-line pt-5">
              <JourneyDateTimePicker
                date={journeyDate}
                departAfter={departAfter}
                today={today}
                maximumDate={maximumDate}
                onDateChange={setJourneyDate}
                onDepartAfterChange={setDepartAfter}
              />
              {schedulesAreApproximate && (
                <p className="mt-3 text-xs leading-[1.55] text-muted">
                  {t('journey.scheduleApproximation')}
                </p>
              )}
            </div>

            <div
              className="mt-5 min-h-15.25 border-t border-line pt-4.75"
              aria-live="polite"
              aria-atomic="true"
            >
              {samePlace ? (
                <p className="text-[13px] leading-normal text-warning">{t('journey.samePlace')}</p>
              ) : origin.place && destination.place ? (
                <>
                  <p className="mb-2 text-[11px] tracking-[1px] text-muted uppercase">
                    {t('journey.selectionTitle')}
                  </p>
                  <p
                    className="flex flex-wrap items-center gap-2.25 text-base font-semibold wrap-anywhere"
                    aria-label={t('journey.selectionSummary', {
                      origin: origin.place.name,
                      destination: destination.place.name,
                    })}
                  >
                    <span className="max-w-full">{origin.place.name}</span>
                    <Icon name="arrow" className="size-5 shrink-0 text-icon-muted" />
                    <span className="max-w-full">{destination.place.name}</span>
                  </p>
                </>
              ) : (
                <p className="text-xs leading-normal text-muted">{t('journey.selectionHint')}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={!canSubmit || isSearching}
              aria-busy={isSearching}
              className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-[700] text-on-accent transition-opacity hover:enabled:opacity-90 disabled:opacity-45"
            >
              <Icon
                name={isSearching ? 'loader' : 'route'}
                size={18}
                className={isSearching ? 'animate-spin motion-reduce:animate-none' : undefined}
              />
              {t('journey.submit')}
              {isSearching && <span className="sr-only">{t('journey.resultsLoading')}</span>}
            </button>
          </form>
        </div>
        <p className="sr-only" role="status" aria-live="polite">
          <span key={swapCount}>{swapCount > 0 ? t('journey.swapped') : ''}</span>
        </p>
      </section>

      {hasSubmittedSearch && !isSearching && (directSearch.isError || directSearch.data) && (
        <section
          className="journey-panel-enter rounded-3xl border border-line bg-surface-card p-6 shadow-(--shadow-card) max-[380px]:p-4.5 min-[850px]:p-8"
          aria-labelledby="journey-results-title"
        >
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

          {directSearch.isError ? (
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
          ) : directSearch.data?.items.length ? (
            <>
              <ol className="mt-4 grid list-none gap-3 p-0">
                {visibleJourneys.map((journey, index) => (
                  <li
                    key={[
                      journey.line_code,
                      journey.departure_time,
                      journey.arrival_time,
                      index,
                    ].join('-')}
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
              {visibleJourneys.length < directSearch.data.items.length && (
                <button
                  type="button"
                  className="mt-4 inline-flex min-h-11 items-center bg-transparent px-1.25 text-sm font-[650] text-accent underline decoration-1 underline-offset-4"
                  onClick={() =>
                    setJourneyResultPage((current) =>
                      current?.fetchedAt === directSearch.data?.fetched_at
                        ? { ...current, page: current.page + 1 }
                        : { fetchedAt: directSearch.data?.fetched_at ?? '', page: 2 },
                    )
                  }
                >
                  {t('journey.showMore')}
                </button>
              )}
            </>
          ) : directSearch.data ? (
            <p className="mt-5 rounded-xl bg-paper px-4 py-4 text-sm leading-[1.6] text-muted">
              {t('journey.resultsEmpty')}
            </p>
          ) : null}
        </section>
      )}
    </main>
  );
}
