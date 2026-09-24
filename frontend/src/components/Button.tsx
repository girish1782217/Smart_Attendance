import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'danger'

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: 'bg-slate-900 text-white hover:bg-slate-800',
  secondary: 'border border-slate-300 text-slate-700 hover:bg-slate-50',
  danger: 'bg-red-600 text-white hover:bg-red-700',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  isLoading?: boolean
}

export function Button({ variant = 'primary', isLoading = false, disabled, children, className = '', ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      className={`rounded-md px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60 ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {isLoading ? 'Please wait…' : children}
    </button>
  )
}
