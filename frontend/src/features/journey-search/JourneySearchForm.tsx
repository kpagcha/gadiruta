/** Render the editable direct-journey form while the page owns URL and query state. */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/Button';
import { Icon } from '../../components/Icon';
import { JourneyDateTimePicker } from './JourneyDateTimePicker';
import { PlaceAutocomplete } from './PlaceAutocomplete';
import type { PlaceFieldValue } from './PlaceAutocomplete';

/** Values and callbacks that let the page coordinate an editable direct-journey search. */
interface JourneySearchFormProps {
  origin: PlaceFieldValue;
  destination: PlaceFieldValue;
  date: string;
  departAfter: string;
  today: string;
  maximumDate: string;
  isSearching: boolean;
  schedulesAreApproximate: boolean;
  onOriginChange: (value: PlaceFieldValue) => void;
  onDestinationChange: (value: PlaceFieldValue) => void;
  onDateChange: (value: string) => void;
  onDepartAfterChange: (value: string) => void;
  onSwap: () => void;
  onSubmit: () => void;
}

/** Render selected-place controls and announce local form feedback accessibly. */
export function JourneySearchForm({
  origin,
  destination,
  date,
  departAfter,
  today,
  maximumDate,
  isSearching,
  schedulesAreApproximate,
  onOriginChange,
  onDestinationChange,
  onDateChange,
  onDepartAfterChange,
  onSwap,
  onSubmit,
}: JourneySearchFormProps) {
  const { t } = useTranslation();
  const [swapCount, setSwapCount] = useState(0);
  const samePlace = origin.place !== null && origin.place.id === destination.place?.id;
  const canSubmit = origin.place !== null && destination.place !== null && !samePlace;

  /** Delegate swapping to the page and announce that the two fields exchanged values. */
  function swapPlaces(): void {
    onSwap();
    setSwapCount((count) => count + 1);
  }

  /** Prevent a browser navigation and allow the page to start or refresh the request. */
  function submitJourney(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form onSubmit={submitJourney}>
      <PlaceAutocomplete
        label={t('journey.origin')}
        placeholder={t('journey.originPlaceholder')}
        clearLabel={t('journey.clearOrigin')}
        value={origin}
        onChange={onOriginChange}
        endpoint="origin"
      />
      <div className="flex min-h-16 items-center justify-end gap-3">
        <span className="h-px flex-1 translate-y-3.5 bg-line-subtle" aria-hidden="true" />
        <Button
          variant="outlinedIcon"
          className="size-11 translate-y-3.5"
          aria-label={t('journey.swap')}
          title={t('journey.swap')}
          disabled={!origin.text && !destination.text}
          onClick={swapPlaces}
        >
          <Icon name="swap" size={20} />
        </Button>
      </div>
      <PlaceAutocomplete
        label={t('journey.destination')}
        placeholder={t('journey.destinationPlaceholder')}
        clearLabel={t('journey.clearDestination')}
        value={destination}
        onChange={onDestinationChange}
        endpoint="destination"
      />

      <div className="mt-7 border-t border-line pt-5">
        <JourneyDateTimePicker
          date={date}
          departAfter={departAfter}
          today={today}
          maximumDate={maximumDate}
          onDateChange={onDateChange}
          onDepartAfterChange={onDepartAfterChange}
        />
        {schedulesAreApproximate && (
          <p className="mt-3 text-xs leading-[1.55] text-muted">
            {t('journey.scheduleApproximation')}
          </p>
        )}
      </div>

      {samePlace ? (
        <div className="mt-5 border-t border-line pt-5" aria-live="polite" aria-atomic="true">
          <p className="text-[13px] leading-normal text-warning">{t('journey.samePlace')}</p>
        </div>
      ) : origin.place && destination.place ? (
        <div className="mt-5 border-t border-line pt-5" aria-live="polite" aria-atomic="true">
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
        </div>
      ) : null}
      <Button
        type="submit"
        className="mt-5 w-full"
        disabled={!canSubmit || isSearching}
        aria-busy={isSearching}
      >
        <Icon
          name={isSearching ? 'loader' : 'route'}
          size={18}
          className={isSearching ? 'animate-spin motion-reduce:animate-none' : undefined}
        />
        {t('journey.submit')}
        {isSearching && <span className="sr-only">{t('journey.resultsLoading')}</span>}
      </Button>
      <p className="sr-only" role="status" aria-live="polite">
        <span key={swapCount}>{swapCount > 0 ? t('journey.swapped') : ''}</span>
      </p>
    </form>
  );
}
