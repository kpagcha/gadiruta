/** Accessible, explicitly selected place suggestions with keyboard and pointer support. */
import { useEffect, useId, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import type { Place } from '../../api/places';
import { Icon } from '../../components/Icon';
import { canSearchPlaces, usePlaceSearch } from './usePlaceSearch';

/** Keep a draft label separate from a confirmed API result; typing invalidates the selection. */
export interface PlaceFieldValue {
  text: string;
  place: Place | null;
}

/** Labels are translated by the caller so the same field can serve either journey endpoint. */
interface PlaceAutocompleteProps {
  label: string;
  placeholder: string;
  clearLabel: string;
  value: PlaceFieldValue;
  onChange: (value: PlaceFieldValue) => void;
  endpoint: 'origin' | 'destination';
}

/** Offer manually selected suggestions while keeping DOM focus in the editable combobox. */
export function PlaceAutocomplete({
  label,
  placeholder,
  clearLabel,
  value,
  onChange,
  endpoint,
}: PlaceAutocompleteProps) {
  const { t, i18n } = useTranslation();
  const id = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const activeRef = useRef<HTMLButtonElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const search = usePlaceSearch(value.text, isOpen && !isComposing);
  const showPopup = isOpen && !isComposing && canSearchPlaces(value.text);
  const isLoading = search.isDebouncing || search.isFetching || search.isPending;
  const options = !isLoading && !search.isError ? (search.data?.items ?? []) : [];
  const activeIndex = options.findIndex((place) => place.id === activeId);
  const activeOption = showPopup ? options[activeIndex] : undefined;
  const listId = `${id}-list`;

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: 'nearest' });
  }, [activeOption?.id]);

  /** Commit a provider result, close suggestions, and return focus from pointer selection. */
  function selectPlace(place: Place): void {
    inputRef.current?.focus();
    onChange({ text: place.name, place });
    setIsOpen(false);
    setActiveId(null);
  }

  /** Clear both draft and confirmed identity, ready for another place search. */
  function clearPlace(): void {
    onChange({ text: '', place: null });
    setActiveId(null);
    inputRef.current?.focus();
    setIsOpen(true);
  }

  /** Navigate only suggestions; leave text editing, tab navigation, and IME input to the browser. */
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.nativeEvent.isComposing || isComposing) return;
    if (event.key === 'Escape') {
      setIsOpen(false);
      setActiveId(null);
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      setIsOpen(true);
      if (!options.length) return;
      const nextIndex =
        event.key === 'ArrowDown'
          ? Math.min(activeIndex + 1, options.length - 1)
          : activeIndex < 0
            ? options.length - 1
            : Math.max(activeIndex - 1, 0);
      setActiveId(options[nextIndex]?.id ?? null);
    } else if (event.key === 'Enter' && activeOption) {
      event.preventDefault();
      selectPlace(activeOption);
    }
  }

  /** Describe current request state without exposing backend error messages. */
  function statusText(): string {
    if (!isOpen) return value.place ? t('places.selected', { name: value.place.name }) : '';
    if (!canSearchPlaces(value.text)) return t('places.minimum');
    if (isLoading) return t('places.loading');
    if (search.isError) return t('places.error');
    if (!options.length) return t('places.empty', { query: value.text.trim() });
    return t('places.results', { count: options.length });
  }

  const fetchedAt = search.data?.fetched_at;
  const endpointMarkClass =
    endpoint === 'destination'
      ? 'size-2.25 rounded-xs border-2 border-accent bg-accent'
      : 'size-2.25 rounded-full border-2 border-accent';

  return (
    <div
      className={`relative min-w-0 ${showPopup ? 'z-5' : ''}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setIsOpen(false);
          setActiveId(null);
        }
      }}
    >
      <label className="mb-2 flex items-center gap-2.25 text-[13px] font-[650]" htmlFor={id}>
        <span className={endpointMarkClass} aria-hidden="true" />
        {label}
      </label>
      <div
        className={`place-field flex items-center rounded-xl border bg-surface-card focus-within:shadow-(--shadow-field-focus) ${value.place ? 'bg-surface-input' : ''}`}
      >
        <input
          ref={inputRef}
          id={id}
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showPopup}
          aria-controls={showPopup ? listId : undefined}
          aria-activedescendant={activeOption ? `${id}-${activeOption.id}` : undefined}
          aria-describedby={`${id}-help ${id}-instructions`}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="none"
          spellCheck={false}
          maxLength={100}
          placeholder={placeholder}
          value={value.text}
          onFocus={() => setIsOpen(value.place === null)}
          onChange={(event) => {
            onChange({ text: event.target.value, place: null });
            setActiveId(null);
            setIsOpen(true);
          }}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          onKeyDown={handleKeyDown}
          className="w-full min-w-0 flex-1 rounded-xl border-0 bg-transparent px-0 py-4.5 pl-4 text-[17px] outline-none placeholder:text-muted-soft focus-visible:outline-offset-0 max-[380px]:pl-3 max-[380px]:text-base"
        />
        {value.text && (
          <button
            type="button"
            className="m-1 grid size-11 shrink-0 place-items-center rounded-lg border-0 bg-transparent text-muted transition-colors hover:bg-surface-hover hover:text-ink"
            aria-label={clearLabel}
            onClick={clearPlace}
          >
            <Icon name="close" size={17} />
          </button>
        )}
        {!value.text && (
          <span className="grid size-12 shrink-0 place-items-center text-icon-muted">
            <Icon name="pin" size={19} />
          </span>
        )}
      </div>
      <p
        id={`${id}-help`}
        className="mt-2 flex min-h-4.5 items-start gap-1 text-xs leading-normal text-muted"
      >
        {value.place ? (
          <>
            <Icon name="check" className="mt-px size-3.75 shrink-0 text-accent" />
            {value.place.municipality ?? value.place.name}
          </>
        ) : (
          t('places.minimum')
        )}
      </p>
      <span id={`${id}-instructions`} className="sr-only">
        {t('places.instructions')}
      </span>
      <span className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {statusText()}
      </span>

      {showPopup && (
        <div className="absolute top-[calc(100%-20px)] right-0 left-0 z-10 overflow-hidden rounded-xl border border-line-popover bg-surface-card shadow-(--shadow-popover)">
          <ul
            id={listId}
            className={`m-0 max-h-68.75 list-none overflow-y-auto overscroll-contain ${options.length ? 'p-1.25' : 'p-0'}`}
            role="listbox"
            aria-label={t('places.suggestions', { field: label })}
          >
            {options.map((place) => (
              <li key={place.id} role="presentation">
                <button
                  ref={place.id === activeOption?.id ? activeRef : undefined}
                  id={`${id}-${place.id}`}
                  type="button"
                  role="option"
                  tabIndex={-1}
                  aria-selected={place.id === activeOption?.id}
                  onMouseDown={(event) => event.preventDefault()}
                  onPointerMove={() => setActiveId(place.id)}
                  onClick={() => selectPlace(place)}
                  className="flex min-h-15 w-full items-center gap-2.5 rounded-[7px] border-0 px-2.25 py-3 text-left hover:bg-surface-selected hover:text-accent-strong aria-selected:bg-surface-selected aria-selected:text-accent-strong"
                >
                  <span className="shrink-0 basis-5.75 text-icon-accent">
                    <Icon name="pin" size={20} />
                  </span>
                  <span className="grid min-w-0 flex-1 gap-0.75 wrap-anywhere">
                    <span className="text-[15px] font-semibold">{place.name}</span>
                    {place.municipality && (
                      <span className="text-xs text-muted">{place.municipality}</span>
                    )}
                  </span>
                  <Icon name="arrow" className="size-4 shrink-0 text-icon-strong" />
                </button>
              </li>
            ))}
          </ul>
          {isLoading ? (
            <p className="flex items-center gap-2.5 px-4.5 py-4.5 text-sm leading-normal wrap-anywhere text-muted">
              <Icon
                name="loader"
                className="size-3.75 shrink-0 animate-spin text-accent motion-reduce:animate-none"
              />
              {t('places.loading')}
            </p>
          ) : search.isError ? (
            <div className="block px-4.5 py-4.5 text-sm leading-normal wrap-anywhere text-muted">
              <p>{t('places.error')}</p>
              <button
                type="button"
                className="mt-2 inline-flex min-h-11 items-center bg-transparent px-1.25 text-sm font-[650] text-accent underline decoration-1 underline-offset-4"
                onClick={() => void search.refetch()}
              >
                {t('places.retry')}
              </button>
            </div>
          ) : !options.length ? (
            <p className="flex items-center gap-2.5 px-4.5 py-4.5 text-sm leading-normal wrap-anywhere text-muted">
              {t('places.empty', { query: value.text.trim() })}
            </p>
          ) : fetchedAt ? (
            <p className="border-t border-line-subtle px-3.5 py-2.5 text-[11px] leading-normal text-muted">
              {t('places.fetchedAt', {
                time: new Intl.DateTimeFormat(i18n.resolvedLanguage, {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                }).format(new Date(fetchedAt)),
              })}
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
