import { createCrudApi } from './crudFactory'

export interface Program {
  id: number
  name: string
  code: string
  department_id: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProgramCreate {
  name: string
  code: string
  department_id: number
}

export interface ProgramUpdate {
  name?: string
  code?: string
  is_active?: boolean
}

export const programsApi = createCrudApi<Program, ProgramCreate, ProgramUpdate>('/api/v1/programs')
