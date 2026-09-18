/** Provide timezone-safe calendar operations for the reusable date and time picker. */

/** Parse an ISO calendar date without letting the browser timezone change its displayed day. */
export function parseCalendarDate(value: string): Date {
  const [year = 0, month = 1, day = 1] = value.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

/** Encode a UTC calendar date in the ISO form accepted by the application API. */
export function formatCalendarDate(value: Date): string {
  return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, '0')}-${String(
    value.getUTCDate(),
  ).padStart(2, '0')}`;
}

/** Extract a sortable year-month key from an ISO calendar date. */
export function monthKey(value: string): string {
  return value.slice(0, 7);
}

/** Move one calendar view forward or backward without crossing a timezone boundary. */
export function shiftMonth(value: string, amount: number): string {
  const [year = 0, month = 1] = value.split('-').map(Number);
  const shifted = new Date(Date.UTC(year, month - 1 + amount, 1));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth() + 1).padStart(2, '0')}`;
}

/** Return ISO dates for all days in a month, padded by the Monday-first weekday offset. */
export function calendarDays(value: string): Array<string | null> {
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
