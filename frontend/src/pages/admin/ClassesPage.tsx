import { useQuery } from '@tanstack/react-query'

import { academicClassesApi, type AcademicClass } from '../../api/academicClasses'
import { programsApi } from '../../api/programs'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function ClassesPage() {
  const { data: programs, isLoading } = useQuery({
    queryKey: ['programs', 'all'],
    queryFn: () => programsApi.list({ page_size: 100 }),
  })

  if (isLoading) return <LoadingState label="Loading programs…" />

  const programOptions = (programs?.items ?? []).map((program) => ({ value: program.id, label: program.name }))
  const programNameById = new Map((programs?.items ?? []).map((program) => [program.id, program.name]))

  const columns: DataTableColumn<AcademicClass>[] = [
    { key: 'name', label: 'Name' },
    { key: 'program_id', label: 'Program', render: (row) => programNameById.get(row.program_id) ?? '—' },
  ]

  const fields: MasterDataField[] = [
    { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'Year 2' },
    {
      name: 'program_id',
      label: 'Program',
      type: 'select',
      required: true,
      numeric: true,
      options: programOptions,
      lockedAfterCreate: true,
    },
  ]

  return (
    <MasterDataManager
      title="Classes"
      description="Manage the academic classes (year groups) within each program."
      resourceLabel="Class"
      queryKey="classes"
      listFn={academicClassesApi.list}
      createFn={academicClassesApi.create}
      updateFn={academicClassesApi.update}
      deactivateFn={academicClassesApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'program_id', label: 'Programs', options: programOptions }}
    />
  )
}
