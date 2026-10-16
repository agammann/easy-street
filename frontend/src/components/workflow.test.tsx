import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Editor } from './Editor'
import { Outline } from './Outline'
import { Upload } from './Upload'
import type { Config, Course, Document, Section } from '../types'
import { api } from '../api'
import App from '../App'

vi.mock('../api', async importOriginal => {
  const original = await importOriginal<typeof import('../api')>()
  return { ...original, api: { ...original.api, config: vi.fn(), courses: vi.fn(), documents: vi.fn(), course: vi.fn(), document: vi.fn(), job: vi.fn(), saveSection: vi.fn(), reorder: vi.fn(), estimate: vi.fn(), approve: vi.fn(), upload: vi.fn(), sample: vi.fn(), versions: vi.fn() } }
})
const quiz: Section = { id: 'q1', kind: 'quiz', title: 'Check your understanding', body: 'What should a fair comparison hold constant?', answer: 'ANSWER_CANARY', explanation: 'EXPLANATION_CANARY', evidence: [{ passage_id: 'p1', quote: 'Change one thing.' }], support_status: 'needs_review', review_notes: ['A verifier quoted ANSWER_CANARY.'], edited: false, order: 0 }
const course: Course = { id: 'c1', document_id: 'd1', title: 'A useful chapter', difficulty: 'introductory', mode: 'demo', options: { modules: 1, assignments: 1, quizzes: 1, questions_per_quiz: 1 }, outline: { title: 'A useful chapter', module_title: 'Make a fair comparison', objectives: ['Compare clearly'], distribution: [{ module: 1, assignments: 1, quizzes: 1, questions: 1 }], warnings: [] }, outline_approved: false, status: 'complete', sections: [quiz], review_flags: ['Global flag leaks ANSWER_CANARY.'], created_at: '2026-10-15T00:00:00Z', updated_at: '2026-10-15T00:00:00Z', version: 1 }
const document: Document = { id: 'd1', filename: 'chapter.txt', sha256: 'hash', format: 'txt', created_at: course.created_at, warnings: [], is_sample: true, passages: [{ id: 'p1', document_id: 'd1', text: 'Change one thing. <script>alert(1)</script>', location: 'Paragraph 1', page: null, paragraph: 1, heading: 'Fair comparisons' }] }
const config: Config = { provider: 'openai', model: 'model', key_configured: true, pricing: { input_per_million: 1, output_per_million: 2, cached_input_per_million: 0.1, updated: '2026-10-15' }, budget: { limit_usd: 10, remaining_usd: 10, reserved_usd: 0, spent_usd: 0 }, privacy_notice: '', milestone: { modules: 1, assignments: 1, quizzes: 1, max_questions: 5 } }

beforeEach(() => { vi.clearAllMocks(); localStorage.clear() })
describe('course review safeguards', () => {
  it('keeps answer fields and verifier answer leaks out of learner view', async () => {
    const user = userEvent.setup()
    render(<Editor course={course} document={document} onCourse={vi.fn()} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.queryByText(/ANSWER_CANARY/)).not.toBeInTheDocument()
    expect(screen.queryByText(/EXPLANATION_CANARY/)).not.toBeInTheDocument()
    expect(screen.getByText(/Quiz needs source review/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Edit' }))
    expect(screen.queryByLabelText('Answer')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Answer explanation')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    await user.click(screen.getByRole('button', { name: 'Answer key' }))
    expect(screen.getByText('ANSWER_CANARY', { exact: true })).toBeVisible()
    expect(screen.getByText('EXPLANATION_CANARY', { exact: true })).toBeVisible()
  })
  it('opens the real supporting passage and renders source text without HTML execution', async () => {
    const user = userEvent.setup()
    const { container } = render(<Editor course={course} document={document} onCourse={vi.fn()} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    await user.click(screen.getByRole('button', { name: 'Show source (1)' }))
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('Paragraph 1')).toBeVisible()
    await user.click(within(dialog).getByText('Read full passage'))
    expect(within(dialog).getByText('Change one thing. <script>alert(1)</script>')).toBeVisible()
    expect(container.querySelector('script')).toBeNull()
  })
  it('saves edits through the backend and reports unsaved editor state', async () => {
    const user = userEvent.setup(), onDirty = vi.fn(), onCourse = vi.fn()
    vi.mocked(api.saveSection).mockResolvedValue({ ...course, version: 2 })
    render(<Editor course={course} document={document} onCourse={onCourse} onRegenerate={vi.fn()} onBack={vi.fn()} onDirty={onDirty}/>)
    await user.click(screen.getByRole('button', { name: 'Edit' }))
    expect(onDirty).toHaveBeenLastCalledWith(true)
    expect(screen.getByRole('button', { name: 'Answer key' })).toBeDisabled()
    await user.clear(screen.getByLabelText('Content'))
    await user.type(screen.getByLabelText('Content'), 'My carefully revised prompt.')
    await user.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(api.saveSection).toHaveBeenCalledWith('c1', 'q1', expect.objectContaining({ body: 'My carefully revised prompt.' })))
    expect(onCourse).toHaveBeenCalledWith(expect.objectContaining({ version: 2 }))
    expect(onDirty).toHaveBeenLastCalledWith(false)
  })
  it('requires outline consent and a cost review before starting generation', async () => {
    const user = userEvent.setup(), onGenerate = vi.fn().mockResolvedValue(undefined)
    vi.mocked(api.estimate).mockResolvedValue({ estimated_max_usd: 0, input_tokens_estimate: 0, output_tokens_limit: 1000, verification_included: true, pricing: config.pricing, budget: config.budget, notice: 'Estimate only.' })
    vi.mocked(api.approve).mockResolvedValue({ ...course, outline_approved: true })
    render(<Outline course={course} config={config} onCourse={vi.fn()} onGenerate={onGenerate} onBack={vi.fn()} busy={false}/>)
    expect(screen.getByRole('button', { name: /Review cost/ })).toBeDisabled()
    expect(api.estimate).not.toHaveBeenCalled()
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: /Review cost/ }))
    expect(onGenerate).not.toHaveBeenCalled()
    await user.click(await screen.findByRole('button', { name: 'Approve & generate' }))
    await waitFor(() => expect(api.approve).toHaveBeenCalledWith('c1'))
    expect(onGenerate).toHaveBeenCalledOnce()
  })
  it('blocks oversized files before making an upload request', async () => {
    const user = userEvent.setup()
    const { container } = render(<Upload onDocument={vi.fn()}/>)
    const file = new File(['small'], 'chapter.pdf', { type: 'application/pdf' })
    Object.defineProperty(file, 'size', { value: 16 * 1024 * 1024 })
    await user.upload(container.querySelector('input[type=file]')!, file)
    expect(screen.getByRole('alert')).toHaveTextContent('larger than 15 MB')
    expect(api.upload).not.toHaveBeenCalled()
  })
  it('resumes a saved course and prevents app navigation from discarding unsaved edits', async () => {
    const user = userEvent.setup()
    localStorage.setItem('easy-street-workspace-v1', JSON.stringify({ courseId: 'c1' }))
    vi.mocked(api.config).mockResolvedValue(config)
    vi.mocked(api.courses).mockResolvedValue([course])
    vi.mocked(api.documents).mockResolvedValue([document])
    vi.mocked(api.course).mockResolvedValue(course)
    vi.mocked(api.document).mockResolvedValue(document)
    render(<App/>)
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    await user.clear(screen.getByLabelText('Content'))
    await user.type(screen.getByLabelText('Content'), 'Keep this unsaved thought.')
    await user.click(screen.getByRole('button', { name: 'Source library' }))
    expect(screen.getByLabelText('Content')).toHaveValue('Keep this unsaved thought.')
    expect(screen.getByRole('alert')).toHaveTextContent('Save or cancel your section edits before leaving')
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    await user.click(screen.getByRole('button', { name: 'Source library' }))
    expect(await screen.findByRole('heading', { name: 'Good ideas live here.' })).toBeVisible()
  })
  it('keeps the edited text recoverable after a save failure', async () => {
    const user = userEvent.setup()
    vi.mocked(api.saveSection).mockRejectedValue(new Error('The local database is unavailable.'))
    render(<Editor course={course} document={document} onCourse={vi.fn()} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    await user.click(screen.getByRole('button', { name: 'Edit' }))
    await user.clear(screen.getByLabelText('Content'))
    await user.type(screen.getByLabelText('Content'), 'Do not lose this change.')
    await user.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('The local database is unavailable.')
    expect(screen.getByLabelText('Content')).toHaveValue('Do not lose this change.')
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeEnabled()
  })
  it('loads completed sections before changing the generation job to complete', async () => {
    const user = userEvent.setup()
    const job = { id: 'j1', course_id: 'c1', section_id: null, status: 'running' as const, stage: 'Generating', error: null, created_at: course.created_at, updated_at: course.updated_at, estimated_max_usd: 0, cancel_requested: false }
    localStorage.setItem('easy-street-workspace-v1', JSON.stringify({ courseId: 'c1', jobId: 'j1' }))
    vi.mocked(api.config).mockResolvedValue(config)
    vi.mocked(api.courses).mockResolvedValue([course])
    vi.mocked(api.documents).mockResolvedValue([document])
    vi.mocked(api.document).mockResolvedValue(document)
    vi.mocked(api.course).mockResolvedValueOnce({ ...course, sections: [], status: 'generating' }).mockResolvedValue(course)
    vi.mocked(api.job).mockResolvedValueOnce(job).mockResolvedValue({ ...job, status: 'complete', stage: 'Complete' })
    render(<App/>)
    expect(await screen.findByRole('heading', { name: 'Good things are taking shape.' })).toBeVisible()
    await user.click(await screen.findByRole('button', { name: 'Review my course' }, { timeout: 4000 }))
    expect(await screen.findByRole('heading', { name: 'Check your understanding' })).toBeVisible()
    expect(screen.queryByRole('heading', { name: 'A plan worth following.' })).not.toBeInTheDocument()
  })
})
