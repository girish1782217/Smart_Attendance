import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export function FormField({ label, error, hint, id, className = '', ...rest }: FormFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, '-')
  const errorId = `${fieldId}-error`
  return (
    <div>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
          error
            ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20'
            : 'border-slate-300 focus:border-brand-500 focus:ring-brand-500/20'
        } ${className}`}
        {...rest}
      />
      {hint && !error && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      {error && (
        <p id={errorId} className="mt-1 text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

export function SelectField({
  label,
  error,
  id,
  children,
  ...rest
}: {
  label: string
  error?: string
  id?: string
  children: ReactNode
} & SelectHTMLAttributes<HTMLSelectElement>) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, '-')
  return (
    <div>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <select
        id={fieldId}
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:outline-none focus:ring-2 ${
          error
            ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20'
            : 'border-slate-300 focus:border-brand-500 focus:ring-brand-500/20'
        }`}
        {...rest}
      >
        {children}
      </select>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
