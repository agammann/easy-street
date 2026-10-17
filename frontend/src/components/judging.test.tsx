import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { api, setCsrfToken } from '../api'
import type { Config, Course, Document, Job } from '../types'
import { SessionGate } from './SessionGate'
import { CourseOptions } from './CourseOptions'
import { Outline } from './Outline'
import { Upload } from './Upload'
import { Settings } from './Settings'
import { CourseLibrary } from './Library'
import { Shell } from './Shell'

const pricing = { input_per_million: 0.49, output_per_million: 1.49, cached_input_per_million: 0.49, updated: '2026-10-16' }
const config: Config = { provider: 'nebius', model: 'nvidia/test-nemotron', key_configured: true, pricing, budget: { limit_usd: 10, spent_usd: 0, reserved_usd: 0, remaining_usd: 10 }, privacy_notice: '', milestone: { modules: 6, assignments: 6, quizzes: 6, max_questions: 5 }, providers: [{ name: 'openai', model: 'openai-test', pricing, key_configured: true }, { name: 'nebius', model: 'nvidia/test-nemotron', pricing, key_configured: true }] }
const document: Document = { id: 'd1', filename: 'chapter.txt', sha256: 'hash', format: 'txt', is_sample: true, warnings: [], created_at: '2026-10-16', passages: [{ id: 'p1', document_id: 'd1', text: 'Record what you notice in a notebook.', heading: 'Garden observations', location: 'Paragraph 1', paragraph: 1, page: null }] }
const course: Course = { id: 'c1', document_id: 'd1', title: 'Garden observations', mode: 'nebius', difficulty: 'introductory', options: { modules: 1, assignments: 1, quizzes: 1, questions_per_quiz: 3 }, outline: { title: 'Garden observations', module_title: 'Observe carefully', objectives: ['Keep useful notes'], distribution: [], warnings: [], selected_passage_ids: ['p1'] }, outline_approved: false, status: 'outline', sections: [], review_flags: [], created_at: '2026-10-16', updated_at: '2026-10-16', version: 1 }
const job: Job = { id: 'j1', course_id: 'c1', section_id: null, status: 'queued', stage: 'queued', error: null, estimated_max_usd: 0.1, cancel_requested: false, created_at: '2026-10-16', updated_at: '2026-10-16' }
const authenticated = { mode: 'judging', authenticated: true, csrf_token: 'test-session-csrf', retention_hours: 24, expires_at: '2026-10-17T15:00:00Z' }
const json = (data: unknown, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => data })
beforeEach(() => { localStorage.clear(); setCsrfToken() })
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); setCsrfToken() })

describe('isolated judging workspace gate', () => {
  it('opens local installations without login or temporary-host claims', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({ mode: 'local', authenticated: true })))
    render(<SessionGate><p>Local course workspace</p></SessionGate>)
    expect(await screen.findByText('Local course workspace')).toBeVisible()
    expect(screen.queryByLabelText('Judging access code')).not.toBeInTheDocument()
    expect(screen.queryByText('Your private judging workspace')).not.toBeInTheDocument()
  })
  it('requires access, sends CSRF only on mutations, and keeps it out of storage', async () => {
    const user = userEvent.setup()
    localStorage.setItem('easy-street-workspace-v1', JSON.stringify({ courseId: 'old-session-course' }))
    const fetchMock = vi.fn().mockResolvedValueOnce(json({ mode: 'judging', authenticated: false, retention_hours: 24 })).mockResolvedValueOnce(json(authenticated)).mockResolvedValue(json(document))
    vi.stubGlobal('fetch', fetchMock)
    render(<SessionGate><p>Protected course workspace</p></SessionGate>)
    expect(screen.queryByText('Protected course workspace')).not.toBeInTheDocument()
    await user.type(await screen.findByLabelText('Judging access code'), 'private-test-access')
    await user.click(screen.getByRole('button', { name: 'Open my private workspace' }))
    expect(await screen.findByText('Protected course workspace')).toBeVisible()
    await api.sample()
    await api.document('d1')
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ access_code: 'private-test-access' })
    expect(fetchMock.mock.calls[1][1].credentials).toBe('same-origin')
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('X-Easy-Street-CSRF')).toBe('test-session-csrf')
    expect(new Headers(fetchMock.mock.calls[3][1].headers).has('X-Easy-Street-CSRF')).toBe(false)
    expect(JSON.stringify(localStorage)).not.toMatch(/test-session-csrf|private-test-access|old-session-course/)
    expect(screen.queryByLabelText(/API key/)).not.toBeInTheDocument()
  })
  it('requires explicit deletion, explains an active-job refusal, and signs out after success', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockResolvedValueOnce(json(authenticated)).mockResolvedValueOnce(json({ detail: 'Cancel the active job before deleting this workspace.' }, 409)).mockResolvedValueOnce({ ok: true, status: 204 })
    vi.stubGlobal('fetch', fetchMock)
    render(<SessionGate><p>Protected course workspace</p></SessionGate>)
    await user.click(await screen.findByRole('button', { name: 'Delete my workspace' }))
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText(/deletes this session’s uploaded documents/)).toBeVisible()
    await user.click(within(dialog).getByRole('button', { name: 'Delete files & sign out' }))
    expect(await within(dialog).findByText('Cancel the active job before deleting this workspace.')).toBeVisible()
    expect(screen.getByText('Protected course workspace')).toBeVisible()
    await user.click(within(dialog).getByRole('button', { name: 'Delete files & sign out' }))
    expect(await screen.findByLabelText('Judging access code')).toBeVisible()
    expect(screen.queryByText('Protected course workspace')).not.toBeInTheDocument()
    expect(fetchMock.mock.calls[2][1].method).toBe('DELETE')
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('X-Easy-Street-CSRF')).toBe('test-session-csrf')
  })
  it('closes protected UI when the server reports an expired session', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(json(authenticated)).mockResolvedValueOnce(json({ detail: 'Session expired.' }, 401)))
    render(<SessionGate><p>Protected course workspace</p></SessionGate>)
    await screen.findByText('Protected course workspace')
    await act(async () => { await expect(api.courses()).rejects.toThrow('Session expired.') })
    expect(await screen.findByLabelText('Judging access code')).toBeVisible()
    expect(screen.queryByText('Protected course workspace')).not.toBeInTheDocument()
    expect(screen.getByText(/Your temporary session has ended/)).toBeVisible()
  })
})

describe('provider selection and one-click licensed sample', () => {
  it('hides unavailable hosted backup import while preserving the local import workflow', () => {
    const { rerender } = render(<CourseLibrary judging courses={[]} onOpen={vi.fn()} onNew={vi.fn()}/>)
    expect(screen.queryByRole('button', { name: 'Import JSON backup' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Import course backup')).not.toBeInTheDocument()
    expect(screen.queryByText(/import a course backup/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Backups preserve course content/)).not.toBeInTheDocument()
    expect(screen.getByText(/Download exports before this temporary workspace expires/)).toBeVisible()
    rerender(<CourseLibrary courses={[]} onOpen={vi.fn()} onNew={vi.fn()}/>)
    expect(screen.getByRole('button', { name: 'Import JSON backup' })).toBeVisible()
    expect(screen.getByLabelText('Import course backup')).toBeInTheDocument()
    expect(screen.getByText(/Backups preserve course content/)).toBeVisible()
  })
  it('uses neutral privacy copy until the hosting configuration is available', () => {
    const { rerender } = render(<Shell view="courses" breadcrumb="New course" onView={vi.fn()} config={null}><p>Loading workspace</p></Shell>)
    expect(screen.getByText(/Only approved source excerpts are sent to your selected provider/)).toBeVisible()
    expect(screen.queryByText(/files stay on your device/)).not.toBeInTheDocument()
    expect(screen.queryByText('Local workspace')).not.toBeInTheDocument()
    expect(screen.queryByText(/go to OpenAI/)).not.toBeInTheDocument()
    rerender(<Shell view="courses" breadcrumb="New course" onView={vi.fn()} config={{ ...config, hosting_mode: 'judging' }}><p>Temporary workspace</p></Shell>)
    expect(screen.getByText(/files stay in an isolated temporary server workspace/)).toBeVisible()
    expect(screen.queryByText(/files stay on your device/)).not.toBeInTheDocument()
  })
  it('preserves both BYO providers and submits the selected Nebius mode', async () => {
    const user = userEvent.setup(), create = vi.spyOn(api, 'createCourse').mockResolvedValue(course)
    render(<CourseOptions document={{ ...document, is_sample: false }} config={{ ...config, provider: 'openai' }} onCourse={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.getByRole('radio', { name: /OpenAI with your own API key/ })).toBeChecked()
    await user.click(screen.getByRole('radio', { name: /Nebius Token Factory with your own API key/ }))
    await user.click(screen.getByRole('button', { name: 'Preview my outline' }))
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ mode: 'nebius', modules: 1, assignments: 1, quizzes: 1, questions_per_quiz: 3 }))
  })
  it('defaults judging to Nebius, hides OpenAI, and preserves the offline sample', () => {
    render(<CourseOptions document={document} config={{ ...config, hosting_mode: 'judging' }} onCourse={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.getByRole('radio', { name: /Nebius Token Factory judging demo/ })).toBeChecked()
    expect(screen.queryByRole('radio', { name: /OpenAI/ })).not.toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Offline demo/ })).toBeVisible()
  })
  it('respects server-advertised judging upload and course caps before requesting generation', async () => {
    const user = userEvent.setup(), upload = vi.spyOn(api, 'upload')
    const judgeConfig: Config = { ...config, hosting_mode: 'judging', demo: { retention_hours: 24, max_upload_mib: 5, max_modules: 2, max_assignments: 2, max_quizzes: 1 } }
    const { container, unmount } = render(<Upload config={judgeConfig} onDocument={vi.fn()}/>)
    const file = new File(['small'], 'chapter.pdf', { type: 'application/pdf' })
    Object.defineProperty(file, 'size', { value: 6 * 1024 * 1024 })
    await user.upload(container.querySelector('input[type="file"]')!, file)
    expect(screen.getByText('This file is larger than 5 MB. Please choose one smaller chapter.')).toBeVisible()
    expect(upload).not.toHaveBeenCalled()
    unmount()
    render(<CourseOptions document={{ ...document, passages: [document.passages[0], { ...document.passages[0], id: 'p2' }, { ...document.passages[0], id: 'p3' }] }} config={judgeConfig} onCourse={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.getByLabelText('Learning modules')).toHaveAttribute('max', '2')
    expect(screen.getByLabelText('Written assignments')).toHaveAttribute('max', '2')
    expect(screen.getByLabelText('Quizzes')).toHaveAttribute('max', '1')
    expect(screen.getByText(/Up to 2 modules, 2 assignments, and 1 quizzes/)).toBeVisible()
  })
  it('discloses the sample provider and retries an uncertain submission with the same ID', async () => {
    const user = userEvent.setup(), onSample = vi.fn()
    const sample = vi.spyOn(api, 'sampleCourse').mockRejectedValueOnce(new Error('Connection lost. Retry safely.')).mockResolvedValueOnce({ course, document, job })
    render(<Upload config={{ ...config, hosting_mode: 'judging' }} onDocument={vi.fn()} onSampleCourse={onSample}/>)
    expect(screen.getByText(/approve sending excerpts of the original garden chapter to Nebius Token Factory/)).toBeVisible()
    expect(screen.getByRole('link', { name: 'sample license' })).toHaveAttribute('href', '/sample-license.txt')
    await user.click(screen.getByRole('button', { name: 'Generate sample with Nebius' }))
    expect(await screen.findByText('Connection lost. Retry safely.')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Generate sample with Nebius' }))
    await waitFor(() => expect(onSample).toHaveBeenCalledWith({ course, document, job }))
    expect(sample.mock.calls[0][0]).toBe(sample.mock.calls[1][0])
  })
  it('keeps normal sample preview independent of the operator-funded workflow', () => {
    render(<Upload config={config} onDocument={vi.fn()} onSampleCourse={vi.fn()}/>)
    expect(screen.getByRole('button', { name: 'Try the sample chapter' })).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Generate sample with Nebius' })).not.toBeInTheDocument()
  })
  it('uses the course provider for consent and key checks when another provider is configured', async () => {
    const user = userEvent.setup()
    vi.spyOn(api, 'estimate').mockResolvedValue({ estimated_max_usd: 0.1, input_tokens_estimate: 100, output_tokens_limit: 1000, verification_included: true, pricing, budget: config.budget, notice: 'Estimate only.' })
    render(<Outline course={course} document={document} config={{ ...config, provider: 'openai', providers: config.providers!.map(provider => ({ ...provider, key_configured: provider.name === 'openai' })) }} onCourse={vi.fn()} onGenerate={vi.fn()} onBack={vi.fn()} busy={false}/>)
    expect(screen.getByRole('checkbox')).toHaveAccessibleName(/sent to Nebius Token Factory using my own API account/)
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: /Review cost/ }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/Selected excerpts will be sent to Nebius Token Factory/)).toBeVisible()
    expect(within(dialog).getByRole('button', { name: 'Approve & generate' })).toBeDisabled()
  })
  it('describes hosted retention and the emergency cutoff without a browser key field', async () => {
    vi.spyOn(api, 'usage').mockResolvedValue({ budget: config.budget, records: [] })
    render(<Settings config={{ ...config, hosting_mode: 'judging', providers: config.providers!.filter(provider => provider.name === 'nebius'), demo: { retention_hours: 24 } }} onRefresh={vi.fn()}/>)
    expect(screen.getByText(/active isolated server workspace expires after 24 hours/)).toBeVisible()
    expect(screen.getByText(/emergency spending cutoff pauses new generation/)).toBeVisible()
    expect(screen.queryByText(/stay on this machine/)).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    await screen.findByText(/No provider usage recorded/)
  })
})
