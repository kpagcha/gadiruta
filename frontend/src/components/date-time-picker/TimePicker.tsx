/** Select an optional clock time from compact, scrollable hour and minute columns. */

import { useEffect, useId, useRef, useState } from 'react';
import { Button } from '../Button';
import { Icon } from '../Icon';

const HOURS = Array.from({ length: 24 }, (_, hour) => String(hour).padStart(2, '0'));
const MINUTE_STEPS = [10, 15] as const;

type MinuteStep = (typeof MINUTE_STEPS)[number];

/** Supply contextual accessibility labels without coupling the picker to one feature's translations. */
export interface TimePickerLabels {
  hours: string;
  minutes: string;
  minuteStep: string;
  tenMinuteSteps: string;
  fifteenMinuteSteps: string;
  clear: string;
}

/** Control one optional local clock value in `HH:mm` form. */
export interface TimePickerProps {
  value: string;
  onChange: (value: string) => void;
  labelledBy: string;
  labels: TimePickerLabels;
}

/** Split a validated optional clock value into independently selectable hour and minute values. */
function splitTime(value: string): [string | null, string | null] {
  const match = /^(\d{2}):(\d{2})$/.exec(value);
  return match ? [match[1] ?? null, match[2] ?? null] : [null, null];
}

/** Return the selectable minute values for a given interval without hardcoding each column. */
function minutesForStep(step: MinuteStep): string[] {
  return Array.from({ length: 60 / step }, (_, index) => String(index * step).padStart(2, '0'));
}

/** Prefer the smallest supported interval that can show an already chosen minute exactly. */
function preferredMinuteStep(minute: string | null): MinuteStep {
  return minute !== null && Number(minute) % 15 !== 0 ? 10 : 15;
}

/** Render a small shadcn-style time popover without requiring a heavyweight time-picker dependency. */
export function TimePicker({ value, onChange, labelledBy, labels }: TimePickerProps) {
  const dialogId = useId();
  const pickerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const selectedHourRef = useRef<HTMLButtonElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedHour, selectedMinute] = splitTime(value);
  const [minuteStep, setMinuteStep] = useState<MinuteStep>(() =>
    preferredMinuteStep(selectedMinute),
  );
  const minutes = minutesForStep(minuteStep);

  useEffect(() => {
    if (!isOpen) return undefined;
    /** Close this focused popover when its controls lose context or the standard close key is pressed. */
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
    if (!isOpen) return;
    selectedHourRef.current?.scrollIntoView({ block: 'nearest' });
  }, [isOpen, selectedHour]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const animationFrame = window.requestAnimationFrame(() => {
      const popover = popoverRef.current;
      if (!popover) return;
      const viewportPadding = 16;
      const overflow =
        popover.getBoundingClientRect().bottom - (window.innerHeight - viewportPadding);
      if (overflow <= 0) return;
      window.scrollBy({
        top: overflow,
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      });
    });

    return () => window.cancelAnimationFrame(animationFrame);
  }, [isOpen]);

  /** Choose an hour while preserving a compatible minute or beginning at the hour. */
  function chooseHour(hour: string): void {
    onChange(
      `${hour}:${selectedMinute && minutes.includes(selectedMinute) ? selectedMinute : '00'}`,
    );
  }

  /** Choose a minute after an hour and close the small popover once the time is complete. */
  function chooseMinute(minute: string): void {
    if (!selectedHour) return;
    onChange(`${selectedHour}:${minute}`);
    setIsOpen(false);
  }

  /** Remove only the optional time while leaving the selected date untouched. */
  function clearTime(): void {
    onChange('');
    setIsOpen(false);
  }

  return (
    <div ref={pickerRef} className="relative">
      <button
        type="button"
        className="flex min-h-11 w-full items-center justify-between rounded-xl border border-line-input bg-surface-input px-3 text-left text-sm font-normal transition-colors outline-none hover:bg-surface-hover focus:border-accent"
        aria-controls={isOpen ? dialogId : undefined}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-labelledby={labelledBy}
        onClick={() => setIsOpen((open) => !open)}
      >
        <span className={value ? 'text-ink tabular-nums' : 'text-muted'}>{value || '--:--'}</span>
        <Icon name="clock" size={18} className="text-icon-muted" />
      </button>

      {isOpen && (
        <div
          id={dialogId}
          ref={popoverRef}
          className="absolute top-[calc(100%+8px)] right-0 z-30 w-52 rounded-xl border border-line-popover bg-surface-card p-2 shadow-(--shadow-popover)"
          role="dialog"
          aria-labelledby={labelledBy}
        >
          <div
            className="mb-2 grid grid-cols-2 gap-1 rounded-lg bg-surface-input p-1"
            role="group"
            aria-label={labels.minuteStep}
          >
            {MINUTE_STEPS.map((step) => (
              <button
                key={step}
                type="button"
                className={`rounded-md px-2 py-1 text-xs font-[650] transition-colors ${
                  minuteStep === step
                    ? 'bg-surface-card text-ink shadow-sm'
                    : 'text-muted hover:text-ink'
                }`}
                aria-pressed={minuteStep === step}
                onClick={() => setMinuteStep(step)}
              >
                {step === 10 ? labels.tenMinuteSteps : labels.fifteenMinuteSteps}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-1.5">
            <div
              className="grid max-h-44 gap-0.5 overflow-y-auto overscroll-contain p-0.5"
              role="group"
              aria-label={labels.hours}
            >
              {HOURS.map((hour) => (
                <button
                  key={hour}
                  ref={selectedHour === hour ? selectedHourRef : undefined}
                  type="button"
                  className={`rounded-lg px-2 py-1.5 text-sm font-[650] tabular-nums transition-colors hover:bg-surface-hover ${
                    selectedHour === hour ? 'bg-accent text-on-accent hover:bg-accent' : ''
                  }`}
                  aria-pressed={selectedHour === hour}
                  onClick={() => chooseHour(hour)}
                >
                  {hour}
                </button>
              ))}
            </div>
            <span className="pb-0.5 text-sm font-[700] text-muted" aria-hidden="true">
              :
            </span>
            <div
              className="grid max-h-44 gap-0.5 overflow-y-auto overscroll-contain p-0.5"
              role="group"
              aria-label={labels.minutes}
            >
              {minutes.map((minute) => (
                <button
                  key={minute}
                  type="button"
                  className={`rounded-lg px-2 py-1.5 text-sm font-[650] tabular-nums transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-35 ${
                    selectedMinute === minute ? 'bg-accent text-on-accent hover:bg-accent' : ''
                  }`}
                  aria-pressed={selectedMinute === minute}
                  disabled={!selectedHour}
                  onClick={() => chooseMinute(minute)}
                >
                  {minute}
                </button>
              ))}
            </div>
          </div>
          {value && (
            <Button variant="text" className="mt-2 min-h-8 px-1.5 text-xs" onClick={clearTime}>
              {labels.clear}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
