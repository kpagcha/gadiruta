/** Choose a direct-journey date and optional departure time from a compact calendar popover. */

import { useEffect, useId, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../components/Icon';

/** Inputs and callbacks owned by the journey search form. */
interface JourneyDateTimePickerProps {
  date: string;
  departAfter: string;
  onDateChange: (date: string) => void;
  onDepartAfterChange: (time: string) => void;
  today: string;
  maximumDate: string;
}

/** Parse an ISO calendar date without letting the browser's timezone change its displayed day. */
function parseCalendarDate(value: string): Date {
  const [year = 0, month = 1, day = 1] = value.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

/** Encode a UTC calendar date in the form required by the public journey API. */
function formatCalendarDate(value: Date): string {
  return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, '0')}-${String(
    value.getUTCDate(),
  ).padStart(2, '0')}`;
}

/** Extract a sortable year-month key from an ISO calendar date. */
function monthKey(value: string): string {
  return value.slice(0, 7);
}

/** Move one calendar view forward or backward without crossing a timezone boundary. */
function shiftMonth(value: string, amount: number): string {
  const [year = 0, month = 1] = value.split('-').map(Number);
  const shifted = new Date(Date.UTC(year, month - 1 + amount, 1));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth() + 1).padStart(2, '0')}`;
}

/** Return ISO dates for all days in a month, padded by the Monday-first weekday offset. */
function calendarDays(value: string): Array<string | null> {
  const [year = 0, month = 1] = value.split('-').map(Number);
  const firstDay = new Date(Date.UTC(year, month - 1, 1));
  const mondayFirstOffset = (firstDay.getUTCDay() + 6) % 7;
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return [
    ...Array<string | null>(mondayFirstOffset).fill(null),
    ...Array.from({ length: lastDay }, (_, index) =>
      formatCalendarDate(new Date(Date.UTC(year, month - 1, index + 1))),
    ),
  ];
}

/** Render a compact calendar-and-time popover that resets back to the immediate journey state. */
export function JourneyDateTimePicker({
  date,
  departAfter,
  onDateChange,
  onDepartAfterChange,
  today,
  maximumDate,
}: JourneyDateTimePickerProps) {
  const { t, i18n } = useTranslation();
  const dialogId = useId();
  const pickerRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [visibleMonth, setVisibleMonth] = useState(monthKey(date));
  const hasCustomSelection = date !== today || Boolean(departAfter);
  const minimumMonth = monthKey(today);
  const maximumMonth = monthKey(maximumDate);
  const formattedDate = new Intl.DateTimeFormat(i18n.resolvedLanguage, {
    month: 'short',
    day: 'numeric',
  }).format(parseCalendarDate(date));
  const chipLabel = !hasCustomSelection
    ? t('journey.now')
    : departAfter
      ? t('journey.dateTimeAt', { date: formattedDate, time: departAfter })
      : formattedDate;
  const monthLabel = new Intl.DateTimeFormat(i18n.resolvedLanguage, {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(parseCalendarDate(`${visibleMonth}-01`));
  const weekdayLabels = Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(i18n.resolvedLanguage, {
      weekday: 'short',
      timeZone: 'UTC',
    }).format(new Date(Date.UTC(2024, 0, index + 1))),
  );

  useEffect(() => {
    if (!isOpen) return undefined;
    /** Close the popover when focus moves away or the standard close key is pressed. */
    function closePopover(event: PointerEvent | KeyboardEvent): void {
      if (event instanceof KeyboardEvent) {
        if (event.key === 'Escape') setIsOpen(false);
        return;
      }
      if (!pickerRef.current?.contains(event.target as Node)) setIsOpen(false);
    }

    document.addEventListener('pointerdown', closePopover);
    document.addEventListener('keydown', closePopover);
    return () => {
      document.removeEventListener('pointerdown', closePopover);
      document.removeEventListener('keydown', closePopover);
    };
  }, [isOpen]);

  /** Restore the default "Now" state after a user has chosen a date or optional time. */
  function resetDateTime(): void {
    onDateChange(today);
    onDepartAfterChange('');
    setIsOpen(false);
  }

  /** Commit a date within CTAN's supported bounds while keeping any optional time filter. */
  function selectDate(nextDate: string): void {
    if (nextDate < today || nextDate > maximumDate) return;
    onDateChange(nextDate);
  }

  /** Open the picker at its selected month, or close it without changing the current selection. */
  function togglePicker(): void {
    if (!isOpen) setVisibleMonth(monthKey(date));
    setIsOpen((open) => !open);
  }

  return (
    <div ref={pickerRef} className="relative">
      <div className="inline-flex min-h-12 items-center rounded-full border border-line-input bg-surface-input p-1 text-[14px] font-[650]">
        <button
          type="button"
          className="inline-flex min-h-10 items-center gap-2 rounded-full px-3 text-ink transition-colors hover:bg-surface-hover"
          aria-controls={isOpen ? dialogId : undefined}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
          aria-label={t('journey.dateTime')}
          onClick={togglePicker}
        >
          <Icon name="clock" size={17} className="text-accent" />
          {chipLabel}
        </button>
        {hasCustomSelection && (
          <button
            type="button"
            className="grid size-10 place-items-center rounded-full text-muted transition-colors hover:bg-surface-hover hover:text-ink"
            aria-label={t('journey.clearDateTime')}
            title={t('journey.clearDateTime')}
            onClick={resetDateTime}
          >
            <Icon name="close" size={16} />
          </button>
        )}
      </div>

      {isOpen && (
        <div
          id={dialogId}
          className="absolute top-[calc(100%+8px)] left-0 z-20 w-[min(20rem,calc(100vw-3rem))] rounded-2xl border border-line-popover bg-surface-card p-4 shadow-(--shadow-popover)"
          role="dialog"
          aria-label={t('journey.dateTimePicker')}
        >
          <div className="mb-3 flex items-center justify-between gap-2">
            <button
              type="button"
              className="grid size-10 place-items-center rounded-full text-muted transition-colors hover:bg-surface-hover hover:text-ink disabled:opacity-35"
              aria-label={t('journey.previousMonth')}
              disabled={visibleMonth <= minimumMonth}
              onClick={() => setVisibleMonth((month) => shiftMonth(month, -1))}
            >
              <Icon name="chevronLeft" size={18} />
            </button>
            <p className="text-sm font-[700]">{monthLabel}</p>
            <button
              type="button"
              className="grid size-10 place-items-center rounded-full text-muted transition-colors hover:bg-surface-hover hover:text-ink disabled:opacity-35"
              aria-label={t('journey.nextMonth')}
              disabled={visibleMonth >= maximumMonth}
              onClick={() => setVisibleMonth((month) => shiftMonth(month, 1))}
            >
              <Icon name="chevronRight" size={18} />
            </button>
          </div>
          <div
            className="grid grid-cols-7 gap-1 text-center text-[11px] font-[650] text-muted"
            aria-hidden="true"
          >
            {weekdayLabels.map((weekday) => (
              <span key={weekday} className="grid size-9 place-items-center">
                {weekday}
              </span>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1" role="grid" aria-label={monthLabel}>
            {calendarDays(visibleMonth).map((calendarDate, index) =>
              calendarDate ? (
                <button
                  key={calendarDate}
                  type="button"
                  role="gridcell"
                  className={`grid size-9 place-items-center rounded-full text-[13px] font-[650] transition-colors hover:bg-surface-hover disabled:cursor-default disabled:opacity-30 ${
                    calendarDate === date
                      ? 'bg-accent text-on-accent hover:bg-accent'
                      : calendarDate === today
                        ? 'border border-accent text-accent'
                        : ''
                  }`}
                  aria-label={new Intl.DateTimeFormat(i18n.resolvedLanguage, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                    timeZone: 'UTC',
                  }).format(parseCalendarDate(calendarDate))}
                  aria-selected={calendarDate === date}
                  disabled={calendarDate < today || calendarDate > maximumDate}
                  onClick={() => selectDate(calendarDate)}
                >
                  {parseCalendarDate(calendarDate).getUTCDate()}
                </button>
              ) : (
                <span key={`blank-${index}`} className="size-9" aria-hidden="true" />
              ),
            )}
          </div>
          <label
            className="mt-4 grid gap-1.5 border-t border-line-subtle pt-4 text-[12px] font-[650]"
            htmlFor={`${dialogId}-time`}
          >
            {t('journey.time')}
            <input
              id={`${dialogId}-time`}
              className="min-h-11 rounded-xl border border-line-input bg-surface-input px-3 text-sm font-normal outline-none focus:border-accent"
              type="time"
              value={departAfter}
              onChange={(event) => onDepartAfterChange(event.target.value)}
            />
          </label>
        </div>
      )}
    </div>
  );
}
