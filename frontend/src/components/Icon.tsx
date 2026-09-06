/** Small code-native icons shared by the place selection interface. */
import type { CSSProperties } from 'react';

/** Available decorative symbols; accessible names belong to their surrounding controls. */
export type IconName = 'route' | 'pin' | 'swap' | 'close' | 'arrow' | 'check';

/** Render a decorative icon without introducing a separate icon-library dependency. */
export function Icon({ name, style }: { name: IconName; style?: CSSProperties }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="24"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={style}
    >
      {name === 'route' && (
        <>
          <circle cx="6" cy="5" r="2" />
          <circle cx="6" cy="19" r="2" />
          <path d="M8 5h7a4 4 0 0 1 0 8h-5a4 4 0 0 0-4 4" />
        </>
      )}
      {name === 'pin' && (
        <>
          <path d="M19 10c0 5-7 10-7 10S5 15 5 10a7 7 0 0 1 14 0Z" />
          <circle cx="12" cy="10" r="2.5" />
        </>
      )}
      {name === 'swap' && (
        <>
          <path d="M8 19V5m-4 4 4-4 4 4m4-4v14m-4-4 4 4 4-4" />
        </>
      )}
      {name === 'close' && <path d="m6 6 12 12M18 6 6 18" />}
      {name === 'arrow' && <path d="M4 12h16m-6-6 6 6-6 6" />}
      {name === 'check' && <path d="m5 12 4 4L19 6" />}
    </svg>
  );
}
