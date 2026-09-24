import { createCrudApi } from './crudFactory'

export interface Department {
  id: number
  name: string
  code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DepartmentCreate {
  name: string
  code: string
}

export interface DepartmentUpdate {
  name?: string
  code?: string
  is_active?: boolean
}

export const departmentsApi = createCrudApi<Department, DepartmentCreate, DepartmentUpdate>('/api/v1/departments')
