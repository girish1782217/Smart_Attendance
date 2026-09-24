import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'

import { ApiError } from '../api/client'
import { useToast } from '../contexts/ToastContext'
import type { Page } from '../types/pagination'
import { Button } from './Button'
import { ConfirmDialog } from './ConfirmDialog'
import { DataTable, type DataTableColumn } from './DataTable'
import { FormField, SelectField } from './FormField'
import { Modal } from './Modal'
import { PageHeader } from './PageHeader'
import { Pagination } from './Pagination'
import { SearchInput } from './SearchInput'
import { StatusBadge } from './StatusBadge'

export interface MasterDataField {
  name: string
  label: string
  type: 'text' | 'number' | 'date' | 'select' | 'password' | 'email'
  required?: boolean
  placeholder?: string
  hint?: string
  min?: number
  max?: number
  options?: { value: number; label: string }[]
  numeric?: boolean // for select: cast the value to a number
  lockedAfterCreate?: boolean // backend's Update schema has no such field -- disable once a row exists
  createOnly?: boolean // e.g. password -- not part of the Update schema at all, hidden once a row exists
}

interface MasterDataRow {
  id: number
  is_active: boolean
}

interface MasterDataManagerProps<T extends MasterDataRow, TCreate, TUpdate> {
  title: string
  description: string
  resourceLabel: string
  queryKey: string
  listFn: (params: Record<string, unknown>) => Promise<Page<T>>
  createFn: (payload: TCreate) => Promise<T>
  updateFn: (id: number, payload: TUpdate) => Promise<T>
  deactivateFn: (id: number) => Promise<T>
  columns: DataTableColumn<T>[]
  fields: MasterDataField[]
  extraFilter?: {
    queryParam: string
    label: string
    options: { value: number; label: string }[]
  }
}

function defaultFormValues(fields: MasterDataField[], row?: Record<string, unknown>): Record<string, string> {
  const values: Record<string, string> = {}
  for (const field of fields) {
    const raw = row?.[field.name]
    values[field.name] = raw === null || raw === undefined ? '' : String(raw)
  }
  return values
}

function parseFieldValue(field: MasterDataField, raw: string): unknown {
  if (field.type === 'number' || (field.type === 'select' && field.numeric)) {
    if (raw === '') return field.required ? undefined : null
    return Number(raw)
  }
  if (raw === '' && !field.required) return null
  return raw
}

function buildPayload(
  fields: MasterDataField[],
  values: Record<string, string>,
  mode: 'create' | 'edit',
): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  for (const field of fields) {
    if (mode === 'edit' && (field.lockedAfterCreate || field.createOnly)) continue
    payload[field.name] = parseFieldValue(field, values[field.name] ?? '')
  }
  return payload
}

export function MasterDataManager<T extends MasterDataRow, TCreate, TUpdate>({
  title,
  description,
  resourceLabel,
  queryKey,
  listFn,
  createFn,
  updateFn,
  deactivateFn,
  columns,
  fields,
  extraFilter,
}: MasterDataManagerProps<T, TCreate, TUpdate>) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [filterValue, setFilterValue] = useState('')
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editingRow, setEditingRow] = useState<T | null>(null)
  const [formValues, setFormValues] = useState<Record<string, string>>({})
  const [isActive, setIsActive] = useState(true)
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deactivateTarget, setDeactivateTarget] = useState<T | null>(null)
  const [isDeactivating, setIsDeactivating] = useState(false)

  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 300)
    return () => clearTimeout(handle)
  }, [searchInput])

  const queryParams: Record<string, unknown> = {
    page,
    page_size: 10,
    search: search || undefined,
  }
  if (extraFilter && filterValue) {
    queryParams[extraFilter.queryParam] = Number(filterValue)
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [queryKey, page, search, filterValue],
    queryFn: () => listFn(queryParams),
  })

  function openCreateModal() {
    setModalMode('create')
    setEditingRow(null)
    setFormValues(defaultFormValues(fields))
    setIsActive(true)
    setFormError(null)
  }

  function openEditModal(row: T) {
    setModalMode('edit')
    setEditingRow(row)
    setFormValues(defaultFormValues(fields, row as unknown as Record<string, unknown>))
    setIsActive(row.is_active)
    setFormError(null)
  }

  function closeModal() {
    setModalMode(null)
    setEditingRow(null)
  }

  async function handleSubmit() {
    setFormError(null)
    setIsSubmitting(true)
    try {
      const payload = buildPayload(fields, formValues, modalMode ?? 'create')
      if (modalMode === 'edit' && editingRow) {
        await updateFn(editingRow.id, { ...payload, is_active: isActive } as TUpdate)
        showToast(`${resourceLabel} updated.`, 'success')
      } else {
        await createFn(payload as TCreate)
        showToast(`${resourceLabel} created.`, 'success')
      }
      await queryClient.invalidateQueries({ queryKey: [queryKey] })
      closeModal()
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleReactivate(row: T) {
    try {
      await updateFn(row.id, { is_active: true } as TUpdate)
      showToast(`${resourceLabel} reactivated.`, 'success')
      await queryClient.invalidateQueries({ queryKey: [queryKey] })
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.', 'error')
    }
  }

  async function handleConfirmDeactivate() {
    if (!deactivateTarget) return
    setIsDeactivating(true)
    try {
      await deactivateFn(deactivateTarget.id)
      showToast(`${resourceLabel} deactivated.`, 'success')
      await queryClient.invalidateQueries({ queryKey: [queryKey] })
      setDeactivateTarget(null)
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.', 'error')
    } finally {
      setIsDeactivating(false)
    }
  }

  const allColumns: DataTableColumn<T>[] = [
    ...columns,
    {
      key: 'is_active',
      label: 'Status',
      render: (row) => <StatusBadge status={row.is_active ? 'ACTIVE' : 'INACTIVE'} />,
    },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-2">
          <Button variant="ghost" className="!px-2 !py-1" onClick={() => openEditModal(row)}>
            Edit
          </Button>
          {row.is_active ? (
            <Button
              variant="ghost"
              className="!px-2 !py-1 text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => setDeactivateTarget(row)}
            >
              Deactivate
            </Button>
          ) : (
            <Button
              variant="ghost"
              className="!px-2 !py-1 text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700"
              onClick={() => void handleReactivate(row)}
            >
              Activate
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title={title}
        description={description}
        action={
          <Button onClick={openCreateModal}>
            <Plus className="h-4 w-4" strokeWidth={2} />
            Add {resourceLabel}
          </Button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <SearchInput value={searchInput} onChange={setSearchInput} placeholder={`Search ${title.toLowerCase()}…`} />
        {extraFilter && (
          <select
            value={filterValue}
            onChange={(event) => {
              setFilterValue(event.target.value)
              setPage(1)
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="">All {extraFilter.label}</option>
            {extraFilter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={allColumns}
          rows={data?.items ?? []}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle={`No ${title.toLowerCase()} found`}
          emptyDescription={search ? 'Try a different search term.' : `Add the first ${resourceLabel.toLowerCase()} to get started.`}
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>

      {modalMode && (
        <Modal title={`${modalMode === 'edit' ? 'Edit' : 'Add'} ${resourceLabel}`} onClose={closeModal}>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              void handleSubmit()
            }}
            className="flex flex-col gap-4"
          >
            {fields.map((field) => {
              if (modalMode === 'edit' && field.createOnly) return null
              const value = formValues[field.name] ?? ''
              const isLocked = modalMode === 'edit' && field.lockedAfterCreate
              const hint = isLocked ? "Can't be changed after creation." : field.hint
              if (field.type === 'select') {
                return (
                  <SelectField
                    key={field.name}
                    label={field.label}
                    required={field.required}
                    value={value}
                    disabled={isLocked}
                    onChange={(event) => setFormValues((prev) => ({ ...prev, [field.name]: event.target.value }))}
                  >
                    <option value="" disabled>
                      Select {field.label.toLowerCase()}…
                    </option>
                    {field.options?.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </SelectField>
                )
              }
              return (
                <FormField
                  key={field.name}
                  label={field.label}
                  type={field.type}
                  required={field.required}
                  placeholder={field.placeholder}
                  hint={hint}
                  min={field.min}
                  max={field.max}
                  value={value}
                  disabled={isLocked}
                  onChange={(event) => setFormValues((prev) => ({ ...prev, [field.name]: event.target.value }))}
                />
              )
            })}

            {modalMode === 'edit' && (
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(event) => setIsActive(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500/40"
                />
                Active
              </label>
            )}

            {formError && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {formError}
              </p>
            )}

            <div className="mt-2 flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                {modalMode === 'edit' ? 'Save changes' : `Create ${resourceLabel}`}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {deactivateTarget && (
        <ConfirmDialog
          title={`Deactivate ${resourceLabel}`}
          message={`This will deactivate the selected ${resourceLabel.toLowerCase()}. It can be reactivated later. Continue?`}
          confirmLabel="Deactivate"
          danger
          isSubmitting={isDeactivating}
          onConfirm={() => void handleConfirmDeactivate()}
          onCancel={() => setDeactivateTarget(null)}
        />
      )}
    </div>
  )
}
