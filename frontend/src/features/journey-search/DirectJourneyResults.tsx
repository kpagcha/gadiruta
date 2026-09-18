/** Present loading, error, empty, and paginated direct-service search results. */

import { useState } from 'react';
import type { RefObject } from 'react';
import { useTranslation } from 'react-i18next';
import { DirectJourneyRequestError, type DirectJourneysResponse } from '../../api/journeys';
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
  const currentJourneyPage =
    journeyResultPage !== null && journeyResultPage.fetchedAt === data?.fetched_at
      ? journeyResultPage.page
      : 1;
  const visibleJourneys = data
    ? data.items.slice(0, currentJourneyPage * VISIBLE_JOURNEY_COUNT)
    : [];

  /** Translate a direct-search failure without exposing untrusted backend messages. */
  function directSearchError(): string {
    if (!(error instanceof DirectJourneyRequestError)) return t('journey.resultsUnavailable');
    if (error.code === 'journey_place_not_found') return t('journey.resultPlacesChanged');
    if (error.code === 'journey_date_unavailable') return t('journey.resultDateUnavailable');
    return t('journey.resultsUnavailable');
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
          {visibleJourneys.length < data.items.length && (
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
