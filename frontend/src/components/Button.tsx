import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white shadow-sm shadow-brand-600/20 hover:bg-brand-700',
  secondary: 'border border-slate-300 bg-white text-slate-700 shadow-sm hover:bg-slate-50',
  danger: 'bg-red-600 text-white shadow-sm shadow-red-600/20 hover:bg-red-700',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  isLoading?: boolean
}

export function Button({
  variant = 'primary',
  isLoading = false,
  disabled,
  children,
  className = '',
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {isLoading ? 'Please wait…' : children}
    </button>
  )
}
