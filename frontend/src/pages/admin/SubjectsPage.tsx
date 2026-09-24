import { useQuery } from '@tanstack/react-query'

import { departmentsApi } from '../../api/departments'
import { subjectsApi, type Subject } from '../../api/subjects'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function SubjectsPage() {
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

  const columns: DataTableColumn<Subject>[] = [
    { key: 'name', label: 'Name' },
    { key: 'code', label: 'Code' },
    { key: 'department_id', label: 'Department', render: (row) => departmentNameById.get(row.department_id) ?? '—' },
    { key: 'credits', label: 'Credits', render: (row) => (row.credits ?? '—').toString(), align: 'right' },
  ]

  const fields: MasterDataField[] = [
    { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'Data Structures' },
    { name: 'code', label: 'Code', type: 'text', required: true, placeholder: 'CS201' },
    {
      name: 'department_id',
      label: 'Department',
      type: 'select',
      required: true,
      numeric: true,
      options: departmentOptions,
      lockedAfterCreate: true,
    },
    { name: 'credits', label: 'Credits', type: 'number', min: 1, max: 20, placeholder: '4' },
  ]

  return (
    <MasterDataManager
      title="Subjects"
      description="Manage subjects taught within each department."
      resourceLabel="Subject"
      queryKey="subjects"
      listFn={subjectsApi.list}
      createFn={subjectsApi.create}
      updateFn={subjectsApi.update}
      deactivateFn={subjectsApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'department_id', label: 'Departments', options: departmentOptions }}
    />
  )
}
