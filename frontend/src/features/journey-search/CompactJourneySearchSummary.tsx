/** Present the collapsed mobile journey search as an actionable route summary. */

import { useTranslation } from 'react-i18next';
import type { Place } from '../../api/places';
import { Icon } from '../../components/Icon';

/** Confirmed places and callbacks required by the compact mobile search view. */
interface CompactJourneySearchSummaryProps {
  origin: Place;
  destination: Place;
  schedulesAreApproximate: boolean;
  onChangeSearch: () => void;
}

/** Render a compact journey summary that expands back into the editable form on demand. */
export function CompactJourneySearchSummary({
  origin,
  destination,
  schedulesAreApproximate,
  onChangeSearch,
}: CompactJourneySearchSummaryProps) {
  const { t } = useTranslation();

  return (
    <div className="desktop:hidden">
      <button
        type="button"
        className="grid w-full gap-3 rounded-2xl bg-surface-input p-3 text-left"
        aria-label={t('journey.selectionSummary', {
          origin: origin.name,
          destination: destination.name,
        })}
        onClick={onChangeSearch}
      >
        <span className="flex min-w-0 items-center gap-2 text-sm font-[700] wrap-anywhere">
          <span className="min-w-0 truncate">{origin.name}</span>
          <Icon name="arrow" className="size-4 shrink-0 text-icon-muted" />
          <span className="min-w-0 truncate">{destination.name}</span>
        </span>
        <span className="text-xs font-[650] text-accent">{t('journey.changeSearch')}</span>
      </button>
      {schedulesAreApproximate && (
        <p className="mt-3 text-xs leading-[1.55] text-muted">
          {t('journey.scheduleApproximation')}
        </p>
      )}
    </div>
  );
}
