/** Smoothly reveal a newly requested result region when its heading is outside the viewport. */

import { useEffect, useRef } from 'react';

/** Coordinate an explicit submit action with the next rendered result state. */
export function useScrollToResults(isSearching: boolean) {
  const resultsPanelRef = useRef<HTMLElement>(null);
  const shouldScrollToResultsRef = useRef(false);

  useEffect(() => {
    if (!isSearching || !shouldScrollToResultsRef.current) return undefined;
    const animationFrame = window.requestAnimationFrame(() => {
      shouldScrollToResultsRef.current = false;
      const resultsPanel = resultsPanelRef.current;
      if (!resultsPanel) return;
      const viewportPadding = 16;
      const { top } = resultsPanel.getBoundingClientRect();
      if (top >= viewportPadding && top <= window.innerHeight - viewportPadding) return;
      resultsPanel.scrollIntoView({
        block: 'start',
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      });
    });

    return () => window.cancelAnimationFrame(animationFrame);
  }, [isSearching]);

  /** Mark the next loading result as a manual submit that may need viewport positioning. */
  function requestResultsScroll(): void {
    shouldScrollToResultsRef.current = true;
  }

  return { resultsPanelRef, requestResultsScroll };
}
