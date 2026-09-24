import { createCrudApi } from './crudFactory'

export interface AcademicYear {
  id: number
  name: string
  start_date: string
  end_date: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AcademicYearCreate {
  name: string
  start_date: string
  end_date: string
}

export interface AcademicYearUpdate {
  name?: string
  start_date?: string
  end_date?: string
  is_active?: boolean
}

export const academicYearsApi = createCrudApi<AcademicYear, AcademicYearCreate, AcademicYearUpdate>(
  '/api/v1/academic-years',
)
