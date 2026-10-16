import type { Config, Course, Document, DocumentSummary, Estimate, Job, Usage, Version, Budget } from './types'

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, { ...options, headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers } })
  if (!response.ok) {
    let message = `The request could not be completed (${response.status}).`
    try { const error = await response.json(); if (typeof error.detail === 'string') message = error.detail } catch { /* HTTP fallback */ }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}
const post = <T,>(path: string, data?: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(data ?? {}) })
const patch = <T,>(path: string, data: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(data) })
const pendingGenerationIds = new Map<string, string>()
async function generate(courseId: string, sectionId?: string) {
  const storageKey = `easy-street-generation-v1:${JSON.stringify([courseId, sectionId ?? null])}`
  let requestId = pendingGenerationIds.get(storageKey)
  if (!requestId) {
    try { requestId = localStorage.getItem(storageKey) || undefined } catch { /* Memory fallback when storage is unavailable. */ }
  }
  requestId ||= crypto.randomUUID()
  pendingGenerationIds.set(storageKey, requestId)
  try { localStorage.setItem(storageKey, requestId) } catch { /* Keep the in-memory ID for safe retry. */ }
  // Keep this ID after a transport error: the backend may already have accepted the job.
  const job = await post<Job>(`/courses/${courseId}/generate`, { idempotency_key: requestId, ...(sectionId ? { section_id: sectionId } : {}) })
  pendingGenerationIds.delete(storageKey)
  try { localStorage.removeItem(storageKey) } catch { /* Storage is optional. */ }
  return job
}
export const api = {
  config: () => request<Config>('/config'),
  courses: () => request<Course[]>('/courses'),
  documents: () => request<DocumentSummary[]>('/documents'),
  document: (id: string) => request<Document>(`/documents/${encodeURIComponent(id)}`),
  course: (id: string) => request<Course>(`/courses/${encodeURIComponent(id)}`),
  courseJob: (id: string) => request<Job | null>(`/courses/${encodeURIComponent(id)}/job`),
  sample: () => post<Document>('/documents/sample'),
  upload: (file: File, ocrPages?: number[]) => { const body = new FormData(); body.append('file', file); if (ocrPages?.length) body.append('ocr_pages', JSON.stringify(ocrPages)); return request<Document>('/documents', { method: 'POST', body }) },
  importCourse: (file: File) => { const body = new FormData(); body.append('file', file); return request<Course>('/courses/import', { method: 'POST', body }) },
  archiveCourse: (id: string, archived: boolean) => post<Course>(`/courses/${id}/archive`, { archived }),
  restoreVersion: (id: string, versionId: number) => post<Course>(`/courses/${id}/restore`, { version_id: versionId }),
  reattachSource: (id: string, file: File) => { const body = new FormData(); body.append('file', file); return request<Course>(`/courses/${id}/source`, { method: 'POST', body }) },
  createCourse: (data: unknown) => post<Course>('/courses', data),
  updateOutline: (id: string, data: unknown) => patch<Course>(`/courses/${id}/outline`, data),
  approve: (id: string) => post<Course>(`/courses/${id}/approve`, { provider_disclosure_accepted: true }),
  estimate: (id: string, sectionId?: string) => request<Estimate>(`/courses/${id}/estimate${sectionId ? `?section_id=${encodeURIComponent(sectionId)}` : ''}`),
  generate,
  job: (id: string) => request<Job>(`/jobs/${id}`),
  cancel: (id: string) => post<Job>(`/jobs/${id}/cancel`),
  resume: (id: string) => post<Job>(`/jobs/${id}/resume`),
  saveSection: (courseId: string, sectionId: string, data: unknown) => patch<Course>(`/courses/${courseId}/sections/${sectionId}`, data),
  reorder: (id: string, ids: string[]) => post<Course>(`/courses/${id}/reorder`, { section_ids: ids }),
  versions: (id: string) => request<Version[]>(`/courses/${id}/versions`),
  usage: () => request<{ budget: Budget; records: Usage[] }>('/usage'),
  exportUrl: (id: string, format: 'html' | 'answers' | 'json') => `/api/courses/${id}/export?format=${format}`,
}
export const money = (value: number) => value > 0 && value < 0.000001 ? '<$0.000001' : `$${value.toFixed(value > 0 && value < 0.0001 ? 6 : value > 0 && value < 0.01 ? 4 : 2)}`
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Something went wrong. Please try again.'
