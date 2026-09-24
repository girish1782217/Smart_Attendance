import { academicYearsApi, type AcademicYear } from '../../api/academicYears'
import type { DataTableColumn } from '../../components/DataTable'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

const columns: DataTableColumn<AcademicYear>[] = [
  { key: 'name', label: 'Name' },
  { key: 'start_date', label: 'Start Date' },
  { key: 'end_date', label: 'End Date' },
]

const fields: MasterDataField[] = [
  { name: 'name', label: 'Name', type: 'text', required: true, placeholder: '2025-2026' },
  { name: 'start_date', label: 'Start Date', type: 'date', required: true },
  { name: 'end_date', label: 'End Date', type: 'date', required: true },
]

export function AcademicYearsPage() {
  return (
    <MasterDataManager
      title="Academic Years"
      description="Manage the academic years used to organize semesters."
      resourceLabel="Academic Year"
      queryKey="academic-years"
      listFn={academicYearsApi.list}
      createFn={academicYearsApi.create}
      updateFn={academicYearsApi.update}
      deactivateFn={academicYearsApi.deactivate}
      columns={columns}
      fields={fields}
    />
  )
}
