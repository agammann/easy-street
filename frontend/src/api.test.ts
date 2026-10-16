import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api'

afterEach(() => { vi.unstubAllGlobals(); localStorage.clear() })

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
