import { createCrudApi } from './crudFactory'

export interface Section {
  id: number
  name: string
  class_id: number
  capacity: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SectionCreate {
  name: string
  class_id: number
  capacity?: number | null
}

export interface SectionUpdate {
  name?: string
  capacity?: number | null
  is_active?: boolean
}

export const sectionsApi = createCrudApi<Section, SectionCreate, SectionUpdate>('/api/v1/sections')
