import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { ApiError } from '../../api/client'
import { settingsApi } from '../../api/settings'
import { Button } from '../../components/Button'
import { ErrorState } from '../../components/ErrorState'
import { FormField } from '../../components/FormField'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { useToast } from '../../contexts/ToastContext'

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['settings', 'low-attendance-threshold'],
    queryFn: settingsApi.getThreshold,
  })

  const [value, setValue] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (data) setValue(String(data.threshold))
  }, [data])

  if (isLoading) return <LoadingState label="Loading settings…" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />

  async function handleSubmit() {
    setFormError(null)
    const numeric = Number(value)
    if (!value || Number.isNaN(numeric) || numeric <= 0 || numeric > 100) {
      setFormError('Enter a threshold between 0 and 100.')
      return
    }
    setIsSaving(true)
    try {
      await settingsApi.setThreshold(numeric)
      showToast('Low-attendance threshold updated.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Settings" description="Configure college-wide attendance settings." />

      <div className="max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Low-Attendance Threshold</h2>
        <p className="mt-1 text-sm text-slate-500">
          Students whose overall attendance falls below this percentage are flagged as low-attendance across
          dashboards and reports.
        </p>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            void handleSubmit()
          }}
          className="mt-4 flex items-end gap-3"
        >
          <div className="flex-1">
            <FormField
              label="Threshold (%)"
              type="number"
              min={0.1}
              max={100}
              step="0.1"
              value={value}
              onChange={(event) => setValue(event.target.value)}
            />
          </div>
          <Button type="submit" isLoading={isSaving}>
            Save
          </Button>
        </form>
        {formError && <p className="mt-3 text-sm text-red-600">{formError}</p>}
      </div>
    </div>
  )
}
