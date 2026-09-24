import { useQuery } from '@tanstack/react-query'

import { academicYearsApi } from '../../api/academicYears'
import { semestersApi, type Semester } from '../../api/semesters'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function SemestersPage() {
  const { data: academicYears, isLoading } = useQuery({
    queryKey: ['academic-years', 'all'],
    queryFn: () => academicYearsApi.list({ page_size: 100 }),
  })

  if (isLoading) return <LoadingState label="Loading academic years…" />

  const yearOptions = (academicYears?.items ?? []).map((year) => ({ value: year.id, label: year.name }))
  const yearNameById = new Map((academicYears?.items ?? []).map((year) => [year.id, year.name]))

  const columns: DataTableColumn<Semester>[] = [
    { key: 'name', label: 'Name' },
    { key: 'academic_year_id', label: 'Academic Year', render: (row) => yearNameById.get(row.academic_year_id) ?? '—' },
    { key: 'start_date', label: 'Start Date' },
    { key: 'end_date', label: 'End Date' },
  ]

  const fields: MasterDataField[] = [
    { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'Semester 1' },
    {
      name: 'academic_year_id',
      label: 'Academic Year',
      type: 'select',
      required: true,
      numeric: true,
      options: yearOptions,
      lockedAfterCreate: true,
    },
    { name: 'start_date', label: 'Start Date', type: 'date', required: true },
    { name: 'end_date', label: 'End Date', type: 'date', required: true },
  ]

  return (
    <MasterDataManager
      title="Semesters"
      description="Manage semesters within each academic year."
      resourceLabel="Semester"
      queryKey="semesters"
      listFn={semestersApi.list}
      createFn={semestersApi.create}
      updateFn={semestersApi.update}
      deactivateFn={semestersApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'academic_year_id', label: 'Academic Years', options: yearOptions }}
    />
  )
}
