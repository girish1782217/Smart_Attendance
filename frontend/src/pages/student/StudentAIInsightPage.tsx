import { useQuery } from '@tanstack/react-query'
import { AlertCircle, Sparkles } from 'lucide-react'

import { aiInsightApi } from '../../api/aiInsight'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { useAuth } from '../../contexts/AuthContext'

function formatPercentage(value: number | null): string {
  return value === null ? 'No data' : `${value}%`
}

export function StudentAIInsightPage() {
  const { user } = useAuth()
  const studentId = user?.student_id

  if (!studentId) {
    return <ErrorState error={new Error('No student profile is linked to this account.')} />
  }

  return <StudentAIInsightContent studentId={studentId} />
}

function StudentAIInsightContent({ studentId }: { studentId: number }) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['ai-insight', studentId],
    queryFn: () => aiInsightApi.get(studentId),
  })

  if (isLoading) return <LoadingState label="Generating your insight…" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />
  if (!data) return null

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="AI Insight" description="An AI-generated summary of your attendance, grounded in your real data." />

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {data.ai_available && data.insight_text ? (
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <Sparkles className="h-5 w-5" strokeWidth={2} />
            </div>
            <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">{data.insight_text}</p>
          </div>
        ) : (
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <AlertCircle className="h-5 w-5" strokeWidth={2} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">AI insight isn't available right now.</p>
              <p className="mt-1 text-sm text-slate-500">
                {data.ai_error_code
                  ? `Reason: ${data.ai_error_code}. Your attendance summary below is still accurate.`
                  : 'Your attendance summary below is still accurate.'}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Overall Attendance</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{formatPercentage(data.overall.percentage)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Present</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-700">{data.overall.present_count}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Absent</p>
          <p className="mt-2 text-2xl font-semibold text-red-700">{data.overall.absent_count}</p>
        </div>
      </div>

      {data.by_subject.length > 0 && (
        <div className="overflow-hidden overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Subject</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Percentage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.by_subject.map((subject) => (
                <tr key={subject.subject_id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 text-slate-900">
                    {subject.subject_name} <span className="text-slate-400">({subject.subject_code})</span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium tabular-nums text-slate-900">
                    {formatPercentage(subject.percentage)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
