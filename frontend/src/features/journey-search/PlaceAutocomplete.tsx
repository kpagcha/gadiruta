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

  return (
    <div
      className={`place-field ${showPopup ? 'place-field--open' : ''}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setIsOpen(false);
          setActiveId(null);
        }
      }}
    >
      <label className="field-label" htmlFor={id}>
        <span className={`endpoint-mark endpoint-mark--${endpoint}`} aria-hidden="true" />
        {label}
      </label>
      <div className={`input-shell ${value.place ? 'input-shell--selected' : ''}`}>
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
        />
        {value.text && (
          <button
            type="button"
            className="clear-button"
            aria-label={clearLabel}
            onClick={clearPlace}
          >
            <Icon name="close" />
          </button>
        )}
        {!value.text && (
          <span className="input-icon">
            <Icon name="pin" />
          </span>
        )}
      </div>
      <p id={`${id}-help`} className="field-help">
        {value.place ? (
          <>
            <Icon name="check" />
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
        <div className="suggestions-panel">
          <ul id={listId} role="listbox" aria-label={t('places.suggestions', { field: label })}>
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
                >
                  <span className="suggestion-icon">
                    <Icon name="pin" />
                  </span>
                  <span className="suggestion-text">
                    <span className="suggestion-name">{place.name}</span>
                    {place.municipality && (
                      <span className="suggestion-municipality">{place.municipality}</span>
                    )}
                  </span>
                  <Icon name="arrow" />
                </button>
              </li>
            ))}
          </ul>
          {isLoading ? (
            <p className="suggestion-message">
              <span className="spinner" aria-hidden="true" />
              {t('places.loading')}
            </p>
          ) : search.isError ? (
            <div className="suggestion-message suggestion-message--error">
              <p>{t('places.error')}</p>
              <button type="button" className="text-button" onClick={() => void search.refetch()}>
                {t('places.retry')}
              </button>
            </div>
          ) : !options.length ? (
            <p className="suggestion-message">{t('places.empty', { query: value.text.trim() })}</p>
          ) : fetchedAt ? (
            <p className="suggestions-fetched">
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
