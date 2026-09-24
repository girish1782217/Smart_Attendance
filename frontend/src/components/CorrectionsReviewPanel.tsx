import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { ApiError } from '../api/client'
import { correctionsApi, type Correction, type CorrectionRequestStatus } from '../api/corrections'
import { useToast } from '../contexts/ToastContext'
import { Button } from './Button'
import { DataTable, type DataTableColumn } from './DataTable'
import { Modal } from './Modal'
import { PageHeader } from './PageHeader'
import { Pagination } from './Pagination'
import { StatusBadge } from './StatusBadge'

const STATUS_FILTERS: { value: CorrectionRequestStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
]

export function CorrectionsReviewPanel({ title, description }: { title: string; description: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<CorrectionRequestStatus | ''>('')
  const [decisionTarget, setDecisionTarget] = useState<{ correction: Correction; action: 'approve' | 'reject' } | null>(
    null,
  )
  const [decisionReason, setDecisionReason] = useState('')
  const [isDeciding, setIsDeciding] = useState(false)
  const [decisionError, setDecisionError] = useState<string | null>(null)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['corrections', page, statusFilter],
    queryFn: () => correctionsApi.list({ page, page_size: 10, status: statusFilter || undefined }),
  })

  function openDecision(correction: Correction, action: 'approve' | 'reject') {
    setDecisionTarget({ correction, action })
    setDecisionReason('')
    setDecisionError(null)
  }

  async function handleConfirmDecision() {
    if (!decisionTarget) return
    setIsDeciding(true)
    setDecisionError(null)
    try {
      if (decisionTarget.action === 'approve') {
        await correctionsApi.approve(decisionTarget.correction.id, decisionReason)
        showToast('Correction approved.', 'success')
      } else {
        await correctionsApi.reject(decisionTarget.correction.id, decisionReason)
        showToast('Correction rejected.', 'success')
      }
      await queryClient.invalidateQueries({ queryKey: ['corrections'] })
      setDecisionTarget(null)
    } catch (err) {
      setDecisionError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsDeciding(false)
    }
  }

  const columns: DataTableColumn<Correction>[] = [
    { key: 'student_name', label: 'Student' },
    {
      key: 'change',
      label: 'Change',
      render: (row) => (
        <span>
          <StatusBadge status={row.original_status} /> <span className="text-slate-400">→</span>{' '}
          <StatusBadge status={row.requested_status} />
        </span>
      ),
    },
    { key: 'reason', label: 'Reason', render: (row) => <span className="line-clamp-2 max-w-xs">{row.reason}</span> },
    { key: 'requested_by_name', label: 'Requested By' },
    { key: 'requested_at', label: 'Requested At', render: (row) => new Date(row.requested_at).toLocaleString() },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) =>
        row.status === 'PENDING' ? (
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              className="!px-2 !py-1 text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700"
              onClick={() => openDecision(row, 'approve')}
            >
              Approve
            </Button>
            <Button
              variant="ghost"
              className="!px-2 !py-1 text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => openDecision(row, 'reject')}
            >
              Reject
            </Button>
          </div>
        ) : (
          <span className="text-xs text-slate-400">{row.reviewed_by_name ? `by ${row.reviewed_by_name}` : '—'}</span>
        ),
    },
  ]

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={title} description={description} />

      <select
        value={statusFilter}
        onChange={(event) => {
          setStatusFilter(event.target.value as CorrectionRequestStatus | '')
          setPage(1)
        }}
        className="w-fit rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
      >
        {STATUS_FILTERS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No correction requests found"
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>

      {decisionTarget && (
        <Modal
          title={decisionTarget.action === 'approve' ? 'Approve Correction' : 'Reject Correction'}
          onClose={() => setDecisionTarget(null)}
        >
          <div className="flex flex-col gap-4">
            <p className="text-sm text-slate-600">
              {decisionTarget.correction.student_name} requested changing this record from{' '}
              <StatusBadge status={decisionTarget.correction.original_status} /> to{' '}
              <StatusBadge status={decisionTarget.correction.requested_status} />.
            </p>
            <div>
              <label htmlFor="decision-reason" className="mb-1.5 block text-sm font-medium text-slate-700">
                Decision note (optional)
              </label>
              <textarea
                id="decision-reason"
                value={decisionReason}
                onChange={(event) => setDecisionReason(event.target.value)}
                rows={3}
                maxLength={1000}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                placeholder="Add a note for the student…"
              />
            </div>
            {decisionError && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {decisionError}
              </p>
            )}
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setDecisionTarget(null)}>
                Cancel
              </Button>
              <Button
                variant={decisionTarget.action === 'reject' ? 'danger' : 'primary'}
                isLoading={isDeciding}
                onClick={() => void handleConfirmDecision()}
              >
                {decisionTarget.action === 'approve' ? 'Approve' : 'Reject'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
