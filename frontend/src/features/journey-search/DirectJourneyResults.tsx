/** Present loading, error, empty, and paginated direct-service search results. */

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { RefObject } from 'react';
import { useTranslation } from 'react-i18next';
import {
  DirectJourneyRequestError,
  fetchDirectJourneys,
  type DirectJourney,
  type DirectJourneysResponse,
} from '../../api/journeys';
import { Button } from '../../components/Button';
import { Panel } from '../../components/Panel';
import { Skeleton } from '../../components/Skeleton';
import { JourneyServiceCard } from './JourneyServiceCard';

const VISIBLE_JOURNEY_COUNT = 4;

/** Track how many services from one fetched result should be visible. */
interface JourneyResultPage {
  fetchedAt: string;
  page: number;
}

/** Keep one complete earlier result segment separate from the complete later result. */
interface EarlierJourneySegment {
  resultKey: string;
  items: DirectJourney[];
}

/** Track how many visual pages from a fetched earlier segment should be visible. */
interface EarlierJourneyPage {
  resultKey: string;
  page: number;
}

/** Identify a response independently of cache timestamps so prior-page state cannot cross searches. */
function journeyResultKey(data: DirectJourneysResponse): string {
  return [
    data.origin.slug,
    data.destination.slug,
    data.date,
    data.depart_after ?? '',
    data.fetched_at,
  ].join('|');
}

/** Identify one displayed service when merging earlier and later result segments without duplicates. */
function journeyKey(journey: DirectJourney): string {
  return [
    journey.line_code,
    journey.departure_time,
    journey.arrival_time,
    journey.duration_minutes,
    journey.note ?? '',
    journey.transport_mode,
  ].join('|');
}

/** Merge visible result segments into one chronological, duplicate-free service list. */
function mergeJourneys(...pages: DirectJourney[][]): DirectJourney[] {
  const journeys = new Map<string, DirectJourney>();
  for (const journey of pages.flat()) journeys.set(journeyKey(journey), journey);
  return [...journeys.values()].sort((first, second) =>
    [first.departure_time, first.arrival_time, first.line_code, first.note ?? '']
      .join('|')
      .localeCompare(
        [second.departure_time, second.arrival_time, second.line_code, second.note ?? ''].join('|'),
      ),
  );
}

/** Inputs the page supplies to render and interact with direct-service results. */
interface DirectJourneyResultsProps {
  panelRef: RefObject<HTMLElement | null>;
  isSearching: boolean;
  error: Error | null;
  data: DirectJourneysResponse | undefined;
  onRetry: () => void;
}

/** Render the semantically ordered direct services and let users reveal successive result pages. */
export function DirectJourneyResults({
  panelRef,
  isSearching,
  error,
  data,
  onRetry,
}: DirectJourneyResultsProps) {
  const { t } = useTranslation();
  const [journeyResultPage, setJourneyResultPage] = useState<JourneyResultPage | null>(null);
  const [earlierJourneySegment, setEarlierJourneySegment] = useState<EarlierJourneySegment | null>(
    null,
  );
  const [earlierJourneyPage, setEarlierJourneyPage] = useState<EarlierJourneyPage | null>(null);
  const [earlierErrorKey, setEarlierErrorKey] = useState<string | null>(null);
  const currentJourneyPage =
    journeyResultPage !== null && journeyResultPage.fetchedAt === data?.fetched_at
      ? journeyResultPage.page
      : 1;
  const resultKey = data ? journeyResultKey(data) : null;
  const currentJourneys = data
    ? data.items.slice(0, currentJourneyPage * VISIBLE_JOURNEY_COUNT)
    : [];
  const earlierJourneys =
    earlierJourneySegment?.resultKey === resultKey ? earlierJourneySegment.items : [];
  const currentEarlierPage =
    earlierJourneyPage?.resultKey === resultKey ? earlierJourneyPage.page : 0;
  const visibleEarlierJourneys = earlierJourneys.slice(
    Math.max(0, earlierJourneys.length - currentEarlierPage * VISIBLE_JOURNEY_COUNT),
  );
  const visibleJourneys = mergeJourneys(visibleEarlierJourneys, currentJourneys);
  const hasEarlierDepartures = data
    ? earlierJourneySegment?.resultKey === resultKey
      ? visibleEarlierJourneys.length < earlierJourneys.length
      : data.has_earlier_departures
    : false;
  const earlierSearch = useMutation({
    mutationFn: (departBefore: string) => {
      if (!data) return Promise.reject(new Error('Direct journey result is unavailable.'));
      return fetchDirectJourneys(
        {
          from: data.origin.slug,
          to: data.destination.slug,
          date: data.date,
          departAfter: null,
          departBefore,
        },
        new AbortController().signal,
      );
    },
  });

  /** Translate a direct-search failure without exposing untrusted backend messages. */
  function directSearchError(): string {
    if (!(error instanceof DirectJourneyRequestError)) return t('journey.resultsUnavailable');
    if (error.code === 'journey_place_not_found') return t('journey.resultPlacesChanged');
    if (error.code === 'journey_date_unavailable') return t('journey.resultDateUnavailable');
    return t('journey.resultsUnavailable');
  }

  /** Fetch the complete earlier segment once, then reveal one earlier visual page per action. */
  async function showEarlierJourneys(): Promise<void> {
    const firstJourney = currentJourneys[0];
    if (!data || !resultKey || !firstJourney) return;
    if (earlierJourneySegment?.resultKey === resultKey) {
      setEarlierJourneyPage((current) => ({
        resultKey,
        page: current?.resultKey === resultKey ? current.page + 1 : 1,
      }));
      setEarlierErrorKey(null);
      return;
    }
    try {
      const earlierResult = await earlierSearch.mutateAsync(
        firstJourney.departure_time.slice(0, 5),
      );
      setEarlierJourneySegment({
        resultKey,
        items: earlierResult.items,
      });
      setEarlierJourneyPage({ resultKey, page: 1 });
      setEarlierErrorKey(null);
    } catch {
      setEarlierErrorKey(resultKey);
    }
  }

  return (
    <Panel
      ref={panelRef}
      className="journey-panel-enter"
      aria-labelledby="journey-results-title"
      aria-busy={isSearching}
    >
      <header>
        <h2 id="journey-results-title" className="text-[21px] font-[650] tracking-[-0.5px]">
          {t('journey.resultsTitle')}
        </h2>
        {!isSearching && data && (
          <p className="mt-1 text-sm text-muted">
            {t('journey.resultsRoute', {
              origin: data.origin.name,
              destination: data.destination.name,
            })}
          </p>
        )}
      </header>

      {isSearching ? (
        <>
          <div className="mt-4 grid gap-3" aria-hidden="true">
            <Skeleton className="h-4 w-35" />
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-30 w-full rounded-xl" />
            ))}
          </div>
          <p className="sr-only" role="status">
            {t('journey.resultsLoading')}
          </p>
        </>
      ) : error ? (
        <div className="mt-5 rounded-xl bg-paper px-4 py-4 text-sm leading-normal text-muted">
          <p>{directSearchError()}</p>
          <Button variant="text" className="mt-2" onClick={onRetry}>
            {t('journey.resultsRetry')}
          </Button>
        </div>
      ) : data?.items.length ? (
        <>
          {hasEarlierDepartures && (
            <div className="mt-4">
              <Button
                variant="text"
                disabled={earlierSearch.isPending}
                onClick={() => void showEarlierJourneys()}
              >
                {earlierSearch.isPending
                  ? t('journey.earlierDeparturesLoading')
                  : t('journey.earlierDepartures')}
              </Button>
              {earlierErrorKey === resultKey && (
                <p className="mt-1 text-sm text-muted" role="status">
                  {t('journey.earlierDeparturesUnavailable')}
                </p>
              )}
            </div>
          )}
          <ol className="mt-4 grid list-none gap-3 p-0">
            {visibleJourneys.map((journey, index) => (
              <li
                key={[journey.line_code, journey.departure_time, journey.arrival_time, index].join(
                  '-',
                )}
              >
                <JourneyServiceCard journey={journey} />
              </li>
            ))}
          </ol>
          {currentJourneys.length < data.items.length && (
            <Button
              variant="text"
              className="mt-4"
              onClick={() =>
                setJourneyResultPage((current) =>
                  current?.fetchedAt === data.fetched_at
                    ? { ...current, page: current.page + 1 }
                    : { fetchedAt: data.fetched_at, page: 2 },
                )
              }
            >
              {t('journey.showMore')}
            </Button>
          )}
        </>
      ) : data ? (
        <p className="mt-5 rounded-xl bg-paper px-4 py-4 text-sm leading-[1.6] text-muted">
          {t('journey.resultsEmpty')}
        </p>
      ) : null}
    </Panel>
  );
}
