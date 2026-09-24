import { createCrudApi } from './crudFactory'

export interface AcademicClass {
  id: number
  name: string
  program_id: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AcademicClassCreate {
  name: string
  program_id: number
}

export interface AcademicClassUpdate {
  name?: string
  is_active?: boolean
}

export const academicClassesApi = createCrudApi<AcademicClass, AcademicClassCreate, AcademicClassUpdate>(
  '/api/v1/classes',
)
