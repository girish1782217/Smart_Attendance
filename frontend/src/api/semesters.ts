import { createCrudApi } from './crudFactory'

export interface Semester {
  id: number
  name: string
  academic_year_id: number
  start_date: string
  end_date: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SemesterCreate {
  name: string
  academic_year_id: number
  start_date: string
  end_date: string
}

export interface SemesterUpdate {
  name?: string
  start_date?: string
  end_date?: string
  is_active?: boolean
}

export const semestersApi = createCrudApi<Semester, SemesterCreate, SemesterUpdate>('/api/v1/semesters')
