/** Share timezone-safe calendar values between journey search controls and page state. */

/** Format the present calendar date in the backend's Europe/Madrid timezone. */
export function madridToday(): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Madrid',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return values.year + '-' + values.month + '-' + values.day;
}

/** Convert an ISO calendar date to a timezone-independent timestamp for date-only comparison. */
export function calendarTimestamp(value: string): number {
  const [year = 0, month = 1, day = 1] = value.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
}
