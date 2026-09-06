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
    <main id="main-content" className="home-layout" tabIndex={-1}>
      <div className="hero-copy">
        <p className="eyebrow">{t('hero.eyebrow')}</p>
        <h1>{t('hero.title')}</h1>
        <p className="hero-description">{t('hero.description')}</p>
        <p className="hero-footnote">
          <span className="little-route" aria-hidden="true">
            <Icon name="route" />
          </span>
          {t('hero.footnote')}
        </p>
      </div>

      <section className="journey-card" aria-labelledby="journey-title">
        <div className="card-heading">
          <h2 id="journey-title">{t('journey.title')}</h2>
          <p>{t('journey.description')}</p>
        </div>
        <div className="place-fields">
          <PlaceAutocomplete
            label={t('journey.origin')}
            placeholder={t('journey.originPlaceholder')}
            clearLabel={t('journey.clearOrigin')}
            value={origin}
            onChange={setOrigin}
            endpoint="origin"
          />
          <div className="swap-row">
            <span aria-hidden="true" />
            <button
              type="button"
              className="swap-button"
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
        <div className="selection-summary" aria-live="polite" aria-atomic="true">
          {samePlace ? (
            <p className="selection-warning">{t('journey.samePlace')}</p>
          ) : origin.place && destination.place ? (
            <>
              <p className="summary-label">{t('journey.selectionTitle')}</p>
              <p
                className="summary-places"
                aria-label={t('journey.selectionSummary', {
                  origin: origin.place.name,
                  destination: destination.place.name,
                })}
              >
                <span>{origin.place.name}</span>
                <Icon name="arrow" />
                <span>{destination.place.name}</span>
              </p>
            </>
          ) : (
            <p className="selection-hint">{t('journey.selectionHint')}</p>
          )}
        </div>
        <p className="sr-only" role="status" aria-live="polite">
          <span key={swapCount}>{swapCount > 0 ? t('journey.swapped') : ''}</span>
        </p>
        <aside className="preview-note">
          <span className="preview-label">{t('journey.previewLabel')}</span>
          <p>{t('journey.previewNotice')}</p>
        </aside>
      </section>
    </main>
  );
}
