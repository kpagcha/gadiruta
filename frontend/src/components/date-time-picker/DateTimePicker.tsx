/** Choose a constrained calendar date and optional time from a reusable popover control. */

import { useEffect, useId, useRef, useState } from 'react';
import { Button } from '../Button';
import { Icon } from '../Icon';
import { calendarDays, monthKey, parseCalendarDate, shiftMonth } from './calendar';
import { TimePicker } from './TimePicker';

/** Supply context-specific wording while keeping the picker independent of any feature namespace. */
export interface DateTimePickerLabels {
  trigger: string;
  now: string;
  formatDateTime: (date: string, time: string) => string;
  clear: string;
  dialog: string;
  previousMonth: string;
  nextMonth: string;
  time: string;
  timeHours: string;
  timeMinutes: string;
  minuteStep: string;
  tenMinuteSteps: string;
  fifteenMinuteSteps: string;
  clearTime: string;
  confirm: string;
}

/** Control a date, optional time, permitted calendar range, locale, and contextual labels. */
export interface DateTimePickerProps {
  date: string;
  time: string;
  onDateChange: (date: string) => void;
  onTimeChange: (time: string) => void;
  today: string;
  maximumDate: string;
  locale: string;
  labels: DateTimePickerLabels;
}

/** Render a compact date/time picker with draft selection and explicit confirmation. */
export function DateTimePicker({
  date,
  time,
  onDateChange,
  onTimeChange,
  today,
  maximumDate,
  locale,
  labels,
}: DateTimePickerProps) {
  const dialogId = useId();
  const pickerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [visibleMonth, setVisibleMonth] = useState(monthKey(date));
  const [draftDate, setDraftDate] = useState(date);
  const [draftTime, setDraftTime] = useState(time);
  const hasCustomSelection = date !== today || Boolean(time);
  const minimumMonth = monthKey(today);
  const maximumMonth = monthKey(maximumDate);
  const formattedDate = new Intl.DateTimeFormat(locale, {
    month: 'short',
    day: 'numeric',
  }).format(parseCalendarDate(date));
  const chipLabel = !hasCustomSelection
    ? labels.now
    : time
      ? labels.formatDateTime(formattedDate, time)
      : formattedDate;
  const monthLabel = new Intl.DateTimeFormat(locale, {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(parseCalendarDate(`${visibleMonth}-01`));
  const weekdayLabels = Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(locale, {
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

  useEffect(() => {
    if (!isOpen) return undefined;
    const animationFrame = window.requestAnimationFrame(() => {
      const popover = popoverRef.current;
      if (!popover) return;
      const viewportPadding = 16;
      const { top, bottom } = popover.getBoundingClientRect();
      const scrollAmount =
        bottom > window.innerHeight - viewportPadding
          ? bottom - (window.innerHeight - viewportPadding)
          : top < viewportPadding
            ? top - viewportPadding
            : 0;

      if (scrollAmount === 0) return;
      window.scrollBy({
        top: scrollAmount,
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      });
    });

    return () => window.cancelAnimationFrame(animationFrame);
  }, [isOpen]);

  /** Restore the supplied immediate state after a user has chosen a date or optional time. */
  function resetDateTime(): void {
    onDateChange(today);
    onTimeChange('');
    setDraftDate(today);
    setDraftTime('');
    setIsOpen(false);
  }

  /** Select a draft date within the caller-supplied bounds while retaining the optional time. */
  function selectDate(nextDate: string): void {
    if (nextDate < today || nextDate > maximumDate) return;
    setDraftDate(nextDate);
  }

  /** Open with the current controlled values as a draft, or discard a draft by closing. */
  function togglePicker(): void {
    if (!isOpen) {
      setVisibleMonth(monthKey(date));
      setDraftDate(date);
      setDraftTime(time);
    }
    setIsOpen((open) => !open);
  }

  /** Apply the draft date and optional time together, then close the picker explicitly. */
  function confirmDateTime(): void {
    onDateChange(draftDate);
    onTimeChange(draftTime);
    setIsOpen(false);
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
          aria-label={labels.trigger}
          onClick={togglePicker}
        >
          <Icon name="clock" size={17} className="text-accent" />
          {chipLabel}
        </button>
        {hasCustomSelection && (
          <Button
            variant="quietIcon"
            className="size-10"
            aria-label={labels.clear}
            title={labels.clear}
            onClick={resetDateTime}
          >
            <Icon name="close" size={16} />
          </Button>
        )}
      </div>

      {isOpen && (
        <div
          id={dialogId}
          ref={popoverRef}
          className="absolute top-[calc(100%+8px)] left-0 z-20 w-[min(20rem,calc(100vw-3rem))] rounded-2xl border border-line-popover bg-surface-card p-4 shadow-(--shadow-popover)"
          role="dialog"
          aria-label={labels.dialog}
        >
          <div className="mb-3 flex items-center justify-between gap-2">
            <Button
              variant="quietIcon"
              className="size-10"
              aria-label={labels.previousMonth}
              disabled={visibleMonth <= minimumMonth}
              onClick={() => setVisibleMonth((month) => shiftMonth(month, -1))}
            >
              <Icon name="chevronLeft" size={18} />
            </Button>
            <p className="text-sm font-[700]">{monthLabel}</p>
            <Button
              variant="quietIcon"
              className="size-10"
              aria-label={labels.nextMonth}
              disabled={visibleMonth >= maximumMonth}
              onClick={() => setVisibleMonth((month) => shiftMonth(month, 1))}
            >
              <Icon name="chevronRight" size={18} />
            </Button>
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
                    calendarDate === draftDate
                      ? 'bg-accent text-on-accent hover:bg-accent'
                      : calendarDate === today
                        ? 'border border-accent text-accent'
                        : ''
                  }`}
                  aria-label={new Intl.DateTimeFormat(locale, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                    timeZone: 'UTC',
                  }).format(parseCalendarDate(calendarDate))}
                  aria-selected={calendarDate === draftDate}
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
          <div className="mt-4 grid gap-1.5 border-t border-line-subtle pt-4 text-[12px] font-[650]">
            <p id={`${dialogId}-time-label`}>{labels.time}</p>
            <TimePicker
              value={draftTime}
              onChange={setDraftTime}
              labelledBy={`${dialogId}-time-label`}
              labels={{
                hours: labels.timeHours,
                minutes: labels.timeMinutes,
                minuteStep: labels.minuteStep,
                tenMinuteSteps: labels.tenMinuteSteps,
                fifteenMinuteSteps: labels.fifteenMinuteSteps,
                clear: labels.clearTime,
              }}
            />
          </div>
          <Button size="compact" className="mt-4 w-full px-4" onClick={confirmDateTime}>
            {labels.confirm}
          </Button>
        </div>
      )}
    </div>
  );
}
