import { createCrudApi } from './crudFactory'

export interface Faculty {
  id: number
  user_id: number
  email: string
  full_name: string
  employee_id: string
  department_id: number
  phone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FacultyCreate {
  email: string
  full_name: string
  password: string
  employee_id: string
  department_id: number
  phone?: string | null
}

export interface FacultyUpdate {
  full_name?: string
  phone?: string | null
  department_id?: number
  is_active?: boolean
}

export const facultyApi = createCrudApi<Faculty, FacultyCreate, FacultyUpdate>('/api/v1/faculty')
