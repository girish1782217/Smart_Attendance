import { createCrudApi } from './crudFactory'

export interface Subject {
  id: number
  name: string
  code: string
  department_id: number
  credits: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SubjectCreate {
  name: string
  code: string
  department_id: number
  credits?: number | null
}

export interface SubjectUpdate {
  name?: string
  code?: string
  credits?: number | null
  is_active?: boolean
}

export const subjectsApi = createCrudApi<Subject, SubjectCreate, SubjectUpdate>('/api/v1/subjects')
