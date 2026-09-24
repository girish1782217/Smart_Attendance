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
      <label htmlFor={fieldId} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
          error ? 'border-red-400' : 'border-slate-300'
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
      <label htmlFor={fieldId} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <select
        id={fieldId}
        className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
          error ? 'border-red-400' : 'border-slate-300'
        }`}
        {...rest}
      >
        {children}
      </select>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
