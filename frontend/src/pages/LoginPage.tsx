import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { Button } from '../components/Button'
import { FormField } from '../components/FormField'
import { useAuth } from '../contexts/AuthContext'

export function LoginPage() {
  const { login, isAuthenticated, isLoading: isSessionLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isSessionLoading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'RATE_LIMITED') {
        setError('Too many failed attempts. Please wait a few minutes and try again.')
      } else if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Smart Attendance</h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to continue</p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4" noValidate>
          <FormField
            label="Email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <FormField
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}
          <Button type="submit" isLoading={isSubmitting} className="w-full">
            Sign in
          </Button>
        </form>
      </div>
    </div>
  )
}
