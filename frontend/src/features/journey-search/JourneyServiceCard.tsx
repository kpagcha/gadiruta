/** Render one normalized direct service as a self-contained timetable entry. */

import { useTranslation } from 'react-i18next';
import type { DirectJourney, TransportMode } from '../../api/journeys';
import { Icon, type IconName } from '../../components/Icon';

/** Render a compact API clock value without applying browser timezone conversion. */
function displayTime(value: string): string {
  return value.slice(0, 5);
}

/** Format an API duration using localized hour and minute fragments. */
function durationText(minutes: number, t: ReturnType<typeof useTranslation>['t']): string {
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (!hours) return t('journey.durationMinutes', { count: remainingMinutes });
  if (!remainingMinutes) return t('journey.durationHours', { count: hours });
  return t('journey.durationHoursMinutes', { hours, minutes: remainingMinutes });
}

/** Select an informative shared icon while keeping unclassified provider values neutral. */
function transportModeIcon(mode: TransportMode): IconName {
  if (mode === 'bus') return 'bus';
  if (mode === 'boat') return 'boat';
  if (mode === 'tram') return 'tram';
  if (mode === 'train' || mode === 'metro') return 'train';
  return 'route';
}

/** Render the line, timing, duration, and provider note for one direct service. */
export function JourneyServiceCard({ journey }: { journey: DirectJourney }) {
  const { t } = useTranslation();

  return (
    <article className="rounded-xl border border-line-subtle bg-surface-input px-4 py-4">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-surface-active px-2 py-1 text-xs font-[700] text-accent">
          <Icon name={transportModeIcon(journey.transport_mode)} size={15} strokeWidth={1.8} />
          {t('journey.line', { line: journey.line_code })}
        </span>
        <span className="text-xs text-muted">{durationText(journey.duration_minutes, t)}</span>
      </div>
      <div className="mt-3 flex items-center gap-3 tabular-nums">
        <time
          className="text-[25px] font-[700] tracking-[-0.8px]"
          dateTime={journey.departure_time}
        >
          {displayTime(journey.departure_time)}
        </time>
        <Icon name="arrow" className="size-5 shrink-0 text-icon-muted" />
        <time className="text-[25px] font-[700] tracking-[-0.8px]" dateTime={journey.arrival_time}>
          {displayTime(journey.arrival_time)}
        </time>
      </div>
      {journey.note && <p className="mt-2.5 text-xs leading-[1.55] text-muted">{journey.note}</p>}
    </article>
  );
}
