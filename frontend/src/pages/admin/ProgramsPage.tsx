import { useQuery } from '@tanstack/react-query'

import { departmentsApi } from '../../api/departments'
import { programsApi, type Program } from '../../api/programs'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function ProgramsPage() {
  const { data: departments, isLoading } = useQuery({
    queryKey: ['departments', 'all'],
    queryFn: () => departmentsApi.list({ page_size: 100 }),
  })

  if (isLoading) return <LoadingState label="Loading departments…" />

  const departmentOptions = (departments?.items ?? []).map((department) => ({
    value: department.id,
    label: department.name,
  }))
  const departmentNameById = new Map((departments?.items ?? []).map((department) => [department.id, department.name]))

  const columns: DataTableColumn<Program>[] = [
    { key: 'name', label: 'Name' },
    { key: 'code', label: 'Code' },
    { key: 'department_id', label: 'Department', render: (row) => departmentNameById.get(row.department_id) ?? '—' },
  ]

  const fields: MasterDataField[] = [
    { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'B.Tech Computer Science' },
    { name: 'code', label: 'Code', type: 'text', required: true, placeholder: 'BTCS' },
    {
      name: 'department_id',
      label: 'Department',
      type: 'select',
      required: true,
      numeric: true,
      options: departmentOptions,
      lockedAfterCreate: true,
    },
  ]

  return (
    <MasterDataManager
      title="Programs"
      description="Manage degree programs offered within each department."
      resourceLabel="Program"
      queryKey="programs"
      listFn={programsApi.list}
      createFn={programsApi.create}
      updateFn={programsApi.update}
      deactivateFn={programsApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'department_id', label: 'Departments', options: departmentOptions }}
    />
  )
}
