/** Render selected-place direct journey search, its shareable URL, and normalized result states. */

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router';
import type { DirectJourneySearchParameters } from '../api/journeys';
import { Icon } from '../components/Icon';
import { Panel } from '../components/Panel';
import { calendarTimestamp, madridToday } from '../features/journey-search/calendar';
import { CompactJourneySearchSummary } from '../features/journey-search/CompactJourneySearchSummary';
import { DirectJourneyResults } from '../features/journey-search/DirectJourneyResults';
import { JourneySearchForm } from '../features/journey-search/JourneySearchForm';
import type { PlaceFieldValue } from '../features/journey-search/PlaceAutocomplete';
import { useScrollToResults } from '../features/journey-search/useScrollToResults';
import {
  hasDirectJourneyParameters,
  useDirectJourneySearch,
} from '../features/journey-search/useDirectJourneySearch';

const APPROXIMATE_SCHEDULE_DAYS = 60;

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
  const [expandedSearchKey, setExpandedSearchKey] = useState<string | null>(null);
  const [searchExecution, setSearchExecution] = useState(0);
  const hydratedSearchRef = useRef<string | null>(null);
  const maximumDate = today.slice(0, 4) + '-12-31';
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
  const { resultsPanelRef, requestResultsScroll } = useScrollToResults(isSearching);
  const hasDirectServices = Boolean(directSearch.data?.items.length);
  const showCompactSearch = hasDirectServices && expandedSearchKey !== submittedSearchKey;
  const schedulesAreApproximate = isScheduleApproximate(journeyDate, today);

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
    if (destination.place && origin.place) searchJourneys(destination, origin);
  }

  /** Start a fresh result execution so local result paging cannot cross a submit or refresh. */
  function refreshJourneySearch(): void {
    setSearchExecution((current) => current + 1);
    void directSearch.refetch();
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
      refreshJourneySearch();
      return;
    }
    setSearchExecution((current) => current + 1);
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

  /** Allow the submit control to refresh the current search in addition to changing its route. */
  function submitJourney(): void {
    requestResultsScroll();
    searchJourneys(origin, destination);
  }

  const pageLayout = hasSubmittedSearch
    ? 'desktop:grid-cols-[0.86fr_1.14fr]'
    : 'desktop:grid-cols-[1fr_1.12fr]';
  const searchPanelClass = hasSubmittedSearch ? 'journey-panel-enter' : undefined;

  return (
    <main
      id="main-content"
      className={
        'grid gap-10 py-12 desktop:items-start desktop:gap-16 desktop:py-20 desktop:pb-21.25 ' +
        pageLayout
      }
      tabIndex={-1}
    >
      {!hasSubmittedSearch && (
        <div className="desktop:pt-8">
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
              className="grid size-9 place-items-center rounded-full border border-line-brand text-accent"
              aria-hidden="true"
            >
              <Icon name="gadiruta" size={21} />
            </span>
            {t('hero.footnote')}
          </p>
        </div>
      )}

      <Panel className={searchPanelClass} aria-label={t('journey.searchForm')}>
        {showCompactSearch && origin.place && destination.place && (
          <CompactJourneySearchSummary
            origin={origin.place}
            destination={destination.place}
            schedulesAreApproximate={schedulesAreApproximate}
            onChangeSearch={() => setExpandedSearchKey(submittedSearchKey)}
          />
        )}

        <div className={showCompactSearch ? 'hidden desktop:block' : ''}>
          <JourneySearchForm
            origin={origin}
            destination={destination}
            date={journeyDate}
            departAfter={departAfter}
            today={today}
            maximumDate={maximumDate}
            isSearching={isSearching}
            schedulesAreApproximate={schedulesAreApproximate}
            onOriginChange={updateOrigin}
            onDestinationChange={updateDestination}
            onDateChange={setJourneyDate}
            onDepartAfterChange={setDepartAfter}
            onSwap={swapPlaces}
            onSubmit={submitJourney}
          />
        </div>
      </Panel>

      {hasSubmittedSearch && (isSearching || directSearch.isError || directSearch.data) && (
        <DirectJourneyResults
          panelRef={resultsPanelRef}
          isSearching={isSearching}
          error={directSearch.error}
          data={directSearch.data}
          searchExecution={searchExecution}
          onRetry={refreshJourneySearch}
        />
      )}
    </main>
  );
}
