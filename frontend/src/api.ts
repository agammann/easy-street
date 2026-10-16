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
export const api = {
  config: () => request<Config>('/config'),
  courses: () => request<Course[]>('/courses'),
  documents: () => request<DocumentSummary[]>('/documents'),
  document: (id: string) => request<Document>(`/documents/${encodeURIComponent(id)}`),
  course: (id: string) => request<Course>(`/courses/${encodeURIComponent(id)}`),
  sample: () => post<Document>('/documents/sample'),
  upload: (file: File) => { const body = new FormData(); body.append('file', file); return request<Document>('/documents', { method: 'POST', body }) },
  createCourse: (data: unknown) => post<Course>('/courses', data),
  updateOutline: (id: string, data: unknown) => patch<Course>(`/courses/${id}/outline`, data),
  approve: (id: string) => post<Course>(`/courses/${id}/approve`, { provider_disclosure_accepted: true }),
  estimate: (id: string, sectionId?: string) => request<Estimate>(`/courses/${id}/estimate${sectionId ? `?section_id=${encodeURIComponent(sectionId)}` : ''}`),
  generate: (id: string, sectionId?: string) => post<Job>(`/courses/${id}/generate`, { idempotency_key: crypto.randomUUID(), ...(sectionId ? { section_id: sectionId } : {}) }),
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
