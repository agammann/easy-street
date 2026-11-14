import { afterEach, expect, it, vi } from 'vitest'
import { api, setCsrfToken } from './api'

afterEach(() => { vi.unstubAllGlobals(); localStorage.clear(); setCsrfToken() })

it('reuses the generation request ID after an uncertain transport failure', async () => {
  const fetchMock = vi.fn()
    .mockRejectedValueOnce(new TypeError('Connection was lost after submission.'))
    .mockResolvedValue({ ok: true, json: async () => ({ id: 'job-one', status: 'queued' }) })
  vi.stubGlobal('fetch', fetchMock)
  await expect(api.generate('retry-course', 'notes')).rejects.toThrow('Connection was lost')
  await api.generate('retry-course', 'notes')
  await api.generate('retry-course', 'notes')
  const keys = fetchMock.mock.calls.map(call => JSON.parse(call[1].body as string).idempotency_key)
  expect(keys[1]).toBe(keys[0])
  expect(keys[2]).not.toBe(keys[1])
})

it('sends explicit sample disclosure and a stable request ID with the in-memory session CSRF token', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ course: {}, document: {}, job: {} }) })
  vi.stubGlobal('fetch', fetchMock)
  setCsrfToken('test-memory-csrf')
  await api.sampleCourse('stable-sample-request')
  expect(fetchMock.mock.calls[0][0]).toBe('/api/sample-course')
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ provider_disclosure_accepted: true, idempotency_key: 'stable-sample-request' })
  expect(new Headers(fetchMock.mock.calls[0][1].headers).get('X-Easy-Street-CSRF')).toBe('test-memory-csrf')
  expect(JSON.stringify(localStorage)).not.toContain('test-memory-csrf')
})
