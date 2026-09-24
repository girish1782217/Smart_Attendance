import { useQuery } from '@tanstack/react-query'

import { departmentsApi } from '../../api/departments'
import { facultyApi, type Faculty } from '../../api/faculty'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function FacultyPage() {
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

  const columns: DataTableColumn<Faculty>[] = [
    { key: 'employee_id', label: 'Employee ID' },
    { key: 'full_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'department_id', label: 'Department', render: (row) => departmentNameById.get(row.department_id) ?? '—' },
    { key: 'phone', label: 'Phone', render: (row) => row.phone ?? '—' },
  ]

  const fields: MasterDataField[] = [
    { name: 'email', label: 'Email', type: 'email', required: true, placeholder: 'faculty@college.edu', lockedAfterCreate: true },
    { name: 'full_name', label: 'Full Name', type: 'text', required: true, placeholder: 'Dr. Jane Doe' },
    {
      name: 'password',
      label: 'Password',
      type: 'password',
      required: true,
      createOnly: true,
      hint: 'Minimum 8 characters. The faculty member can sign in with this immediately.',
    },
    { name: 'employee_id', label: 'Employee ID', type: 'text', required: true, placeholder: 'EMP1001', lockedAfterCreate: true },
    { name: 'department_id', label: 'Department', type: 'select', required: true, numeric: true, options: departmentOptions },
    { name: 'phone', label: 'Phone', type: 'text', placeholder: '+1 555 0100' },
  ]

  return (
    <MasterDataManager
      title="Faculty"
      description="Manage faculty accounts and their department."
      resourceLabel="Faculty Member"
      queryKey="faculty"
      listFn={facultyApi.list}
      createFn={facultyApi.create}
      updateFn={facultyApi.update}
      deactivateFn={facultyApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'department_id', label: 'Departments', options: departmentOptions }}
    />
  )
}
