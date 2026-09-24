import { apiFetch, buildQueryString } from './client'
import type { Page } from '../types/pagination'

/** Mirrors the backend's CRUDBase (SPEC 04): 7+ resources share an
 * identical create/list/get/patch/deactivate shape, so one factory backs
 * all of their API modules instead of repeating the same 5 functions. */
export function createCrudApi<TResponse, TCreate, TUpdate>(basePath: string) {
  return {
    list: (params: Record<string, unknown> = {}) =>
      apiFetch<Page<TResponse>>(`${basePath}${buildQueryString(params)}`),
    get: (id: number) => apiFetch<TResponse>(`${basePath}/${id}`),
    create: (payload: TCreate) =>
      apiFetch<TResponse>(basePath, { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: TUpdate) =>
      apiFetch<TResponse>(`${basePath}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    deactivate: (id: number) => apiFetch<TResponse>(`${basePath}/${id}`, { method: 'DELETE' }),
  }
}
