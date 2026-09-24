import { useQuery } from '@tanstack/react-query'
import { CalendarCheck } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { correctionsApi, type Correction, type CorrectionRequestStatus } from '../../api/corrections'
import { Button } from '../../components/Button'
import { DataTable, type DataTableColumn } from '../../components/DataTable'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { StatusBadge } from '../../components/StatusBadge'

const STATUS_FILTERS: { value: CorrectionRequestStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
]

export function StudentMyCorrectionsPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<CorrectionRequestStatus | ''>('')

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['corrections', 'mine', page, statusFilter],
    queryFn: () => correctionsApi.list({ page, page_size: 10, status: statusFilter || undefined }),
  })

  const columns: DataTableColumn<Correction>[] = [
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
    { key: 'reason', label: 'Reason', render: (row) => <span className="line-clamp-2 max-w-sm">{row.reason}</span> },
    { key: 'requested_at', label: 'Requested At', render: (row) => new Date(row.requested_at).toLocaleString() },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'decision',
      label: 'Decision Note',
      render: (row) =>
        row.status === 'PENDING' ? (
          <span className="text-xs text-slate-400">Awaiting review</span>
        ) : (
          <span className="text-slate-600">
            {row.decision_reason ?? '—'} {row.reviewed_by_name ? `(${row.reviewed_by_name})` : ''}
          </span>
        ),
    },
  ]

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="My Correction Requests"
        description="Track the status of attendance corrections you've requested."
        action={
          <Link to="/student/attendance">
            <Button>
              <CalendarCheck className="h-4 w-4" strokeWidth={2} />
              Request a Correction
            </Button>
          </Link>
        }
      />
      <p className="-mt-3 text-sm text-slate-500">
        Corrections are requested against a specific session record — open{' '}
        <Link to="/student/attendance" className="font-medium text-brand-600 hover:underline">
          My Attendance
        </Link>{' '}
        and use "Request Correction" on the record you want changed.
      </p>

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
          emptyTitle="No correction requests yet"
          emptyDescription="Request a correction from the My Attendance page if a record looks wrong."
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>
    </div>
  )
}
