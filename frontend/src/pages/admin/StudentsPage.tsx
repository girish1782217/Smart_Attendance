import { useQuery } from '@tanstack/react-query'

import { academicClassesApi } from '../../api/academicClasses'
import { sectionsApi } from '../../api/sections'
import { studentsApi, type Student } from '../../api/students'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function StudentsPage() {
  const { data: sections, isLoading: isLoadingSections } = useQuery({
    queryKey: ['sections', 'all'],
    queryFn: () => sectionsApi.list({ page_size: 100 }),
  })
  const { data: classes, isLoading: isLoadingClasses } = useQuery({
    queryKey: ['classes', 'all'],
    queryFn: () => academicClassesApi.list({ page_size: 100 }),
  })

  if (isLoadingSections || isLoadingClasses) return <LoadingState label="Loading sections…" />

  const classNameById = new Map((classes?.items ?? []).map((cls) => [cls.id, cls.name]))
  const sectionLabel = (sectionId: number, sectionName?: string) => {
    const section = sections?.items.find((item) => item.id === sectionId)
    const name = sectionName ?? section?.name ?? '—'
    const className = section ? classNameById.get(section.class_id) : undefined
    return className ? `${className} - ${name}` : name
  }
  const sectionOptions = (sections?.items ?? []).map((section) => ({
    value: section.id,
    label: sectionLabel(section.id, section.name),
  }))

  const columns: DataTableColumn<Student>[] = [
    { key: 'roll_number', label: 'Roll Number' },
    { key: 'full_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'section_id', label: 'Section', render: (row) => sectionLabel(row.section_id) },
    { key: 'phone', label: 'Phone', render: (row) => row.phone ?? '—' },
  ]

  const fields: MasterDataField[] = [
    { name: 'email', label: 'Email', type: 'email', required: true, placeholder: 'student@college.edu', lockedAfterCreate: true },
    { name: 'full_name', label: 'Full Name', type: 'text', required: true, placeholder: 'Jane Doe' },
    {
      name: 'password',
      label: 'Password',
      type: 'password',
      required: true,
      createOnly: true,
      hint: 'Minimum 8 characters. The student can sign in with this immediately.',
    },
    { name: 'roll_number', label: 'Roll Number', type: 'text', required: true, placeholder: 'CSEA001', lockedAfterCreate: true },
    { name: 'section_id', label: 'Section', type: 'select', required: true, numeric: true, options: sectionOptions },
    { name: 'phone', label: 'Phone', type: 'text', placeholder: '+1 555 0100' },
  ]

  return (
    <MasterDataManager
      title="Students"
      description="Manage student accounts and their section enrollment."
      resourceLabel="Student"
      queryKey="students"
      listFn={studentsApi.list}
      createFn={studentsApi.create}
      updateFn={studentsApi.update}
      deactivateFn={studentsApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'section_id', label: 'Sections', options: sectionOptions }}
    />
  )
}
