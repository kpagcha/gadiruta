/** Reuse the small set of action-button treatments in the interface. */

import type { ComponentPropsWithoutRef } from 'react';

/** Name the button appearances that are shared across the current application. */
type ButtonVariant = 'primary' | 'quietIcon' | 'outlinedIcon' | 'text';
type ButtonSize = 'default' | 'compact';

/** Accept native button behavior while applying one deliberate visual treatment. */
interface ButtonProps extends ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-[700] text-on-accent transition-opacity hover:enabled:opacity-90 disabled:opacity-45',
  quietIcon:
    'grid place-items-center rounded-full text-muted transition-colors hover:bg-surface-hover hover:text-ink disabled:opacity-35',
  outlinedIcon:
    'grid place-items-center rounded-full border border-line bg-paper text-accent transition-colors hover:enabled:border-line-hover hover:enabled:bg-surface-hover-strong disabled:opacity-45',
  text: 'inline-flex min-h-11 items-center bg-transparent px-1.25 text-sm font-[650] text-accent underline decoration-1 underline-offset-4',
};

const sizeClasses: Record<ButtonSize, string> = {
  default: 'min-h-12',
  compact: 'min-h-11',
};

/** Render a native button with a shared visual variant and a safe non-submit default. */
export function Button({
  className,
  type = 'button',
  variant = 'primary',
  size = 'default',
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      type={type}
      className={[
        variantClasses[variant],
        variant === 'primary' ? sizeClasses[size] : undefined,
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    />
  );
}
