export type RoleName = 'ADMIN' | 'FACULTY' | 'STUDENT'

export const ROLE_NAMES: RoleName[] = ['ADMIN', 'FACULTY', 'STUDENT']

export function hasRole(roles: RoleName[], role: RoleName): boolean {
  return roles.includes(role)
}
