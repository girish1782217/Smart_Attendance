import { departmentsApi, type Department } from '../../api/departments'
import type { DataTableColumn } from '../../components/DataTable'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

const columns: DataTableColumn<Department>[] = [
  { key: 'name', label: 'Name' },
  { key: 'code', label: 'Code' },
]

const fields: MasterDataField[] = [
  { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'Computer Science' },
  { name: 'code', label: 'Code', type: 'text', required: true, placeholder: 'CSE' },
]

export function DepartmentsPage() {
  return (
    <MasterDataManager
      title="Departments"
      description="Manage the academic departments in your college."
      resourceLabel="Department"
      queryKey="departments"
      listFn={departmentsApi.list}
      createFn={departmentsApi.create}
      updateFn={departmentsApi.update}
      deactivateFn={departmentsApi.deactivate}
      columns={columns}
      fields={fields}
    />
  )
}
