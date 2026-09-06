/** A focused starting point for selecting journey endpoints; no timetable lookup yet. */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Icon } from '../components/Icon';
import { PlaceAutocomplete } from '../features/journey-search/PlaceAutocomplete';
import type { PlaceFieldValue } from '../features/journey-search/PlaceAutocomplete';

/** Preserve both draft labels and confirmed identities when editing or swapping endpoints. */
export function HomePage() {
  const { t } = useTranslation();
  const [origin, setOrigin] = useState<PlaceFieldValue>({ text: '', place: null });
  const [destination, setDestination] = useState<PlaceFieldValue>({ text: '', place: null });
  const [swapCount, setSwapCount] = useState(0);
  const samePlace = origin.place !== null && origin.place.id === destination.place?.id;

  /** Exchange complete field values, including partially typed input, in one React update. */
  function swapPlaces(): void {
    setOrigin(destination);
    setDestination(origin);
    setSwapCount((count) => count + 1);
  }

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

      <section
        className="min-w-0 rounded-3xl border border-line bg-white p-6 shadow-card max-[380px]:p-4.5 min-[850px]:p-8"
        aria-labelledby="journey-title"
      >
        <div className="mb-7.5">
          <h2 id="journey-title" className="text-[23px] font-[650] tracking-[-0.6px]">
            {t('journey.title')}
          </h2>
          <p className="mt-2 text-sm leading-normal text-muted">{t('journey.description')}</p>
        </div>
        <div>
          <PlaceAutocomplete
            label={t('journey.origin')}
            placeholder={t('journey.originPlaceholder')}
            clearLabel={t('journey.clearOrigin')}
            value={origin}
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
            value={destination}
            onChange={setDestination}
            endpoint="destination"
          />
        </div>
        <div
          className="mt-6.75 min-h-15.25 border-t border-line pt-4.75"
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
        <p className="sr-only" role="status" aria-live="polite">
          <span key={swapCount}>{swapCount > 0 ? t('journey.swapped') : ''}</span>
        </p>
        <aside className="mt-5 rounded-[10px] bg-paper px-4 py-3.5">
          <span className="mb-1.25 block text-[11px] font-[650] tracking-[0.8px] uppercase">
            {t('journey.previewLabel')}
          </span>
          <p className="text-xs leading-[1.6] text-muted">{t('journey.previewNotice')}</p>
        </aside>
      </section>
    </main>
  );
}
