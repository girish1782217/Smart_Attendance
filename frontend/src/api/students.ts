import { createCrudApi } from './crudFactory'

export interface Student {
  id: number
  user_id: number
  email: string
  full_name: string
  roll_number: string
  section_id: number
  phone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StudentCreate {
  email: string
  full_name: string
  password: string
  roll_number: string
  section_id: number
  phone?: string | null
}

export interface StudentUpdate {
  full_name?: string
  phone?: string | null
  section_id?: number
  is_active?: boolean
}

export const studentsApi = createCrudApi<Student, StudentCreate, StudentUpdate>('/api/v1/students')
