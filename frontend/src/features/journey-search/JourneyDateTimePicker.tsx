/** Adapt the reusable date and time picker to direct-journey search wording and values. */

import { useTranslation } from 'react-i18next';
import { DateTimePicker } from '../../components/date-time-picker/DateTimePicker';

/** Inputs and callbacks owned by the journey search form. */
interface JourneyDateTimePickerProps {
  date: string;
  departAfter: string;
  onDateChange: (date: string) => void;
  onDepartAfterChange: (time: string) => void;
  today: string;
  maximumDate: string;
}

/** Render direct-journey date/time labels around a feature-neutral picker implementation. */
export function JourneyDateTimePicker({
  date,
  departAfter,
  onDateChange,
  onDepartAfterChange,
  today,
  maximumDate,
}: JourneyDateTimePickerProps) {
  const { t, i18n } = useTranslation();

  return (
    <DateTimePicker
      date={date}
      time={departAfter}
      onDateChange={onDateChange}
      onTimeChange={onDepartAfterChange}
      today={today}
      maximumDate={maximumDate}
      locale={i18n.resolvedLanguage ?? 'en'}
      labels={{
        trigger: t('journey.dateTime'),
        now: t('journey.now'),
        formatDateTime: (formattedDate, time) =>
          t('journey.dateTimeAt', { date: formattedDate, time }),
        clear: t('journey.clearDateTime'),
        dialog: t('journey.dateTimePicker'),
        previousMonth: t('journey.previousMonth'),
        nextMonth: t('journey.nextMonth'),
        time: t('journey.time'),
        timeHours: t('journey.timeHours'),
        timeMinutes: t('journey.timeMinutes'),
        minuteStep: t('journey.minuteStep'),
        tenMinuteSteps: t('journey.tenMinuteSteps'),
        fifteenMinuteSteps: t('journey.fifteenMinuteSteps'),
        clearTime: t('journey.clearTime'),
        confirm: t('journey.confirmDateTime'),
      }}
    />
  );
}
