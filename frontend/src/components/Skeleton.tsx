/** Render a neutral animated placeholder while nearby content is loading. */

/** Visual sizing supplied by the context where the placeholder is used. */
interface SkeletonProps {
  className?: string;
}

/** Render a reusable, decorative loading surface with reduced-motion support. */
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <span
      className={`block animate-pulse rounded-md bg-surface-active motion-reduce:animate-none ${className}`}
      aria-hidden="true"
    />
  );
}
