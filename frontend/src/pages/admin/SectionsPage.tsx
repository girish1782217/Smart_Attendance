import { useQuery } from '@tanstack/react-query'

import { academicClassesApi } from '../../api/academicClasses'
import { sectionsApi, type Section } from '../../api/sections'
import type { DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { MasterDataManager, type MasterDataField } from '../../components/MasterDataManager'

export function SectionsPage() {
  const { data: classes, isLoading } = useQuery({
    queryKey: ['classes', 'all'],
    queryFn: () => academicClassesApi.list({ page_size: 100 }),
  })

  if (isLoading) return <LoadingState label="Loading classes…" />

  const classOptions = (classes?.items ?? []).map((cls) => ({ value: cls.id, label: cls.name }))
  const classNameById = new Map((classes?.items ?? []).map((cls) => [cls.id, cls.name]))

  const columns: DataTableColumn<Section>[] = [
    { key: 'name', label: 'Name' },
    { key: 'class_id', label: 'Class', render: (row) => classNameById.get(row.class_id) ?? '—' },
    { key: 'capacity', label: 'Capacity', render: (row) => (row.capacity ?? '—').toString(), align: 'right' },
  ]

  const fields: MasterDataField[] = [
    { name: 'name', label: 'Name', type: 'text', required: true, placeholder: 'A' },
    {
      name: 'class_id',
      label: 'Class',
      type: 'select',
      required: true,
      numeric: true,
      options: classOptions,
      lockedAfterCreate: true,
    },
    { name: 'capacity', label: 'Capacity', type: 'number', min: 1, placeholder: '60' },
  ]

  return (
    <MasterDataManager
      title="Sections"
      description="Manage sections within each class."
      resourceLabel="Section"
      queryKey="sections"
      listFn={sectionsApi.list}
      createFn={sectionsApi.create}
      updateFn={sectionsApi.update}
      deactivateFn={sectionsApi.deactivate}
      columns={columns}
      fields={fields}
      extraFilter={{ queryParam: 'class_id', label: 'Classes', options: classOptions }}
    />
  )
}
