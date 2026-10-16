import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CourseOptions } from './CourseOptions'
import { Outline } from './Outline'
import { Editor } from './Editor'
import { CourseLibrary } from './Library'
import { DocumentReview } from './DocumentReview'
import { SourceRecovery } from './SourceRecovery'
import { Generation } from './Generation'
import { Upload } from './Upload'
import { api } from '../api'
import type { Config, Course, Document, Job } from '../types'

vi.mock('../api', async importOriginal => {
  const original = await importOriginal<typeof import('../api')>()
  return { ...original, api: { ...original.api, createCourse: vi.fn(), updateOutline: vi.fn(), approve: vi.fn(), estimate: vi.fn(), generate: vi.fn(), importCourse: vi.fn(), archiveCourse: vi.fn(), restoreVersion: vi.fn(), versions: vi.fn(), upload: vi.fn(), reattachSource: vi.fn(), document: vi.fn() } }
})
const document: Document = { id: 'd1', filename: 'chapter.txt', sha256: 'hash', format: 'txt', created_at: '2026-10-15', warnings: [], is_sample: true, passages: ['p1', 'p2', 'p3'].map((id, index) => ({ id, document_id: 'd1', text: `Source passage ${index + 1}. Learn carefully.`, heading: `Idea ${index + 1}`, location: `Paragraph ${index + 1}`, page: null, paragraph: index + 1 })) }
const course: Course = { id: 'c1', document_id: 'd1', title: 'A course in two parts', difficulty: 'introductory', mode: 'demo', options: { modules: 2, assignments: 2, quizzes: 1, questions_per_quiz: 3 }, outline: { title: 'A course in two parts', module_title: 'Begin with questions', objectives: ['Start carefully'], modules: [{ id: 'module-1', title: 'Begin with questions', objectives: ['Start carefully'], selected_passage_ids: ['p1'], assignments: 1, quizzes: 0 }, { id: 'module-2', title: 'Try the ideas', objectives: ['Apply the lesson'], selected_passage_ids: ['p2'], assignments: 1, quizzes: 1 }], distribution: [], warnings: [] }, outline_approved: true, status: 'complete', sections: [{ id: 's1', module_id: 'module-1', kind: 'introduction', title: 'Welcome to the first module', body: 'Start with a question.', answer: null, explanation: null, evidence: [], support_status: 'proposal', review_notes: [], edited: false, order: 0 }, { id: 's2', module_id: 'module-2', kind: 'notes', title: 'Keep a notebook', body: 'Record what you notice.', answer: null, explanation: null, evidence: [], support_status: 'proposal', review_notes: [], edited: false, order: 1 }], review_flags: [], created_at: '2026-10-15', updated_at: '2026-10-15', version: 4 }
const config: Config = { provider: 'openai', model: 'model', key_configured: false, pricing: { input_per_million: 1, output_per_million: 2, cached_input_per_million: 0.1, updated: '2026-10-15' }, budget: { limit_usd: 10, remaining_usd: 10, reserved_usd: 0, spent_usd: 0 }, privacy_notice: '', milestone: { modules: 6, assignments: 6, quizzes: 6, max_questions: 5 } }
beforeEach(() => { vi.resetAllMocks(); localStorage.clear() })

describe('complete course workflow', () => {
  it('sends the chosen course-wide counts and bounds assessments when module count shrinks', async () => {
    const user = userEvent.setup(), onCourse = vi.fn()
    vi.mocked(api.createCourse).mockResolvedValue(course)
    render(<CourseOptions document={document} config={config} onCourse={onCourse} onBack={vi.fn()}/>)
    for (const [label, value] of [['Learning modules', '3'], ['Written assignments', '5'], ['Quizzes', '4'], ['Questions per quiz', '5']]) { await user.clear(screen.getByLabelText(label)); await user.type(screen.getByLabelText(label), value) }
    await user.click(screen.getByRole('button', { name: 'Preview my outline' }))
    expect(api.createCourse).toHaveBeenCalledWith(expect.objectContaining({ modules: 3, assignments: 5, quizzes: 4, questions_per_quiz: 5 }))
    await user.clear(screen.getByLabelText('Learning modules')); await user.type(screen.getByLabelText('Learning modules'), '1')
    expect(screen.getByLabelText('Written assignments')).toHaveValue(2)
    expect(screen.getByLabelText('Quizzes')).toHaveValue(2)
  })
  it('shows uncovered source passages and requires matching assessment totals before saving the outline', async () => {
    const user = userEvent.setup()
    vi.mocked(api.updateOutline).mockResolvedValue(course)
    render(<Outline course={{ ...course, sections: [] }} document={document} config={config} onCourse={vi.fn()} onGenerate={vi.fn()} onBack={vi.fn()} busy={false}/>)
    expect(screen.getByText('2 of 3 passages')).toBeVisible()
    await user.click(screen.getByText('1 passages are outside this outline'))
    expect(screen.getByText('Paragraph 3 · Idea 3')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Edit outline' }))
    await user.clear(screen.getByLabelText('Module 1 assignments')); await user.type(screen.getByLabelText('Module 1 assignments'), '0')
    expect(screen.getByRole('button', { name: 'Save outline' })).toBeDisabled()
    await user.clear(screen.getByLabelText('Module 2 assignments')); await user.type(screen.getByLabelText('Module 2 assignments'), '2')
    const firstModule = screen.getByRole('group', { name: 'Module 1' })
    await user.click(within(firstModule).getByText('Choose source passages · 1 selected'))
    await user.click(within(firstModule).getByRole('checkbox', { name: /Paragraph 3/ }))
    await user.click(screen.getByRole('button', { name: 'Save outline' }))
    expect(api.updateOutline).toHaveBeenCalledWith('c1', expect.objectContaining({ modules: expect.arrayContaining([expect.objectContaining({ id: 'module-1', assignments: 0, selected_passage_ids: ['p1', 'p3'] }), expect.objectContaining({ id: 'module-2', assignments: 2 })]) }))
  })
  it('approves an existing course outline without regenerating or estimating any content', async () => {
    const user = userEvent.setup(), onApproved = vi.fn(), onGenerate = vi.fn()
    vi.mocked(api.approve).mockResolvedValue(course)
    render(<Outline course={{ ...course, outline_approved: false }} document={document} config={config} onCourse={vi.fn()} onGenerate={onGenerate} onApproved={onApproved} onBack={vi.fn()} busy={false}/>)
    expect(screen.getByRole('button', { name: 'Approve outline & return' })).toBeDisabled()
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Approve outline & return' }))
    expect(api.approve).toHaveBeenCalledWith('c1')
    expect(onApproved).toHaveBeenCalledOnce()
    expect(onGenerate).not.toHaveBeenCalled()
    expect(api.estimate).not.toHaveBeenCalled()
  })
  it('groups sections by module and prevents reordering across the module boundary', () => {
    render(<Editor course={course} document={document} onCourse={vi.fn()} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    const section = screen.getByRole('heading', { name: 'Welcome to the first module' }).closest('section')!
    expect(within(section).getByRole('heading', { name: 'Begin with questions' })).toBeVisible()
    expect(within(section).queryByText('Record what you notice.')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Move Welcome to the first module down' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Move Keep a notebook up' })).toBeDisabled()
  })
  it('restores a selected version through the backend and leaves generation untouched', async () => {
    const user = userEvent.setup(), onCourse = vi.fn()
    vi.mocked(api.versions).mockResolvedValue([{ id: 17, created_at: course.created_at, reason: 'Before edit', course }])
    vi.mocked(api.restoreVersion).mockResolvedValue({ ...course, version: 5, outline_approved: false })
    render(<Editor course={course} document={document} onCourse={onCourse} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    await user.click(screen.getByRole('button', { name: 'Version history' }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: /Before edit/ }))
    await user.click(within(dialog).getByRole('button', { name: 'Restore this version' }))
    expect(api.restoreVersion).toHaveBeenCalledWith('c1', 17)
    expect(onCourse).toHaveBeenCalledWith(expect.objectContaining({ version: 5, outline_approved: false }))
    expect(api.generate).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
  it('keeps editing available but disables regeneration when a backup lacks its original source', () => {
    render(<Editor course={{ ...course, source_missing: true }} document={null} onCourse={vi.fn()} onRegenerate={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.getAllByRole('button', { name: 'Edit' }).every(button => !button.hasAttribute('disabled'))).toBe(true)
    expect(screen.getAllByRole('button', { name: 'Regenerate' }).every(button => button.hasAttribute('disabled'))).toBe(true)
  })
  it('imports a backup and opens the returned course without overwriting an existing course', async () => {
    const user = userEvent.setup(), onOpen = vi.fn(), onCourse = vi.fn(), imported = { ...course, id: 'imported', source_missing: true }
    vi.mocked(api.importCourse).mockResolvedValue(imported)
    const { container } = render(<CourseLibrary courses={[course]} onOpen={onOpen} onCourse={onCourse} onNew={vi.fn()}/>)
    const file = new File(['{}'], 'backup.json', { type: 'application/json' })
    await user.upload(container.querySelector('input[type=file]')!, file)
    expect(api.importCourse).toHaveBeenCalledWith(file)
    expect(onOpen).toHaveBeenCalledWith(imported)
    expect(onCourse).toHaveBeenCalledWith(imported)
  })
  it('filters archived courses and lets them return to active courses', async () => {
    const user = userEvent.setup(), onCourse = vi.fn(), archived = { ...course, id: 'archive', title: 'Saved for later', archived: true }
    vi.mocked(api.archiveCourse).mockResolvedValue({ ...archived, archived: false })
    render(<CourseLibrary courses={[course, archived]} onOpen={vi.fn()} onCourse={onCourse} onNew={vi.fn()}/>)
    expect(screen.queryByRole('button', { name: /Saved for later/ })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Archived (1)' }))
    expect(screen.getByRole('button', { name: /Saved for later/ })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Unarchive' }))
    expect(api.archiveCourse).toHaveBeenCalledWith('archive', false)
    expect(onCourse).toHaveBeenCalledWith(expect.objectContaining({ archived: false }))
  })
  it('keeps a failed source restore recoverable and never loads an unrelated document', async () => {
    const user = userEvent.setup(), onAttached = vi.fn()
    vi.mocked(api.reattachSource).mockRejectedValue(new Error('The source file does not match the backup.'))
    const { container } = render(<SourceRecovery course={course} document={document} disabled={false} onAttached={onAttached}/>)
    await user.upload(container.querySelector('input[type=file]')!, new File(['different'], 'wrong.txt', { type: 'text/plain' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('does not match')
    expect(api.document).not.toHaveBeenCalled()
    expect(onAttached).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Restore original source' })).toBeEnabled()
  })
  it('requires explicit page selection for local OCR and blocks course creation for an unreadable preview', async () => {
    const user = userEvent.setup(), onDocument = vi.fn(), file = new File(['pdf'], 'scan.pdf', { type: 'application/pdf' })
    vi.mocked(api.upload).mockResolvedValue(document)
    render(<DocumentReview document={{ ...document, passages: [], format: 'pdf', needs_ocr_pages: [1, 2, 3, 4, 5, 6], insufficient_text: true }} file={file} ocr={{ available: true, max_pages: 5, language: 'eng' }} onDocument={onDocument} onContinue={vi.fn()} onBack={vi.fn()}/>)
    expect(api.upload).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Looks good. Shape my course' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Read selected pages with OCR' })).toBeDisabled()
    for (let page = 1; page <= 5; page++) await user.click(screen.getByRole('checkbox', { name: `Page ${page}` }))
    expect(screen.getByRole('checkbox', { name: 'Page 6' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Read selected pages with OCR' }))
    expect(api.upload).toHaveBeenCalledWith(file, [1, 2, 3, 4, 5])
    expect(onDocument).toHaveBeenCalledWith(document, file)
  })
  it('displays durable module progress and the current module name', () => {
    const job: Job = { id: 'j1', course_id: course.id, section_id: null, status: 'running', stage: 'verification_in_flight', error: null, created_at: course.created_at, updated_at: course.updated_at, estimated_max_usd: 0.5, cancel_requested: false, total_modules: 2, completed_modules: 1, current_module_id: 'module-2' }
    render(<Generation course={course} job={job} onJob={vi.fn()} onOpen={vi.fn()}/>)
    expect(screen.getByRole('progressbar', { name: 'Modules completed' })).toHaveAttribute('value', '1')
    expect(screen.getByText('1 of 2 modules saved')).toBeVisible()
    expect(screen.getByText('In progress').closest('li')).toHaveTextContent('Try the ideas')
  })
  it('continues a partial course through cost approval while keeping its saved modules', async () => {
    const user = userEvent.setup(), onGenerate = vi.fn().mockResolvedValue(undefined), onApproved = vi.fn()
    const partial = { ...course, generated_module_ids: ['module-1'], sections: [course.sections[0]] }
    vi.mocked(api.estimate).mockResolvedValue({ estimated_max_usd: 0, input_tokens_estimate: 0, output_tokens_limit: 100, verification_included: true, pricing: config.pricing, budget: config.budget, notice: '' })
    vi.mocked(api.approve).mockResolvedValue(partial)
    render(<Outline course={partial} document={document} config={config} onCourse={vi.fn()} onGenerate={onGenerate} onApproved={onApproved} onBack={vi.fn()} busy={false}/>)
    expect(screen.getByText(/Continue the remaining 1 module/)).toBeVisible()
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Review cost & continue' }))
    await user.click(await screen.findByRole('button', { name: 'Approve & generate' }))
    expect(onGenerate).toHaveBeenCalledOnce()
    expect(onApproved).not.toHaveBeenCalled()
  })
  it('shows only the requested modules when continuing an interrupted course', () => {
    const job: Job = { id: 'j2', course_id: course.id, section_id: null, status: 'complete', stage: 'complete', error: null, created_at: course.created_at, updated_at: course.updated_at, estimated_max_usd: 0, cancel_requested: false, total_modules: 1, completed_modules: 1, module_ids: ['module-2'] }
    render(<Generation course={{ ...course, generated_module_ids: ['module-1', 'module-2'] }} job={job} onJob={vi.fn()} onOpen={vi.fn()}/>)
    expect(screen.getByText('1 of 1 modules saved')).toBeVisible()
    expect(screen.getByText('Try the ideas')).toBeVisible()
    expect(screen.queryByText('Begin with questions')).not.toBeInTheDocument()
  })
  it('does not reopen an upload after the user leaves the upload page', async () => {
    const user = userEvent.setup(), onDocument = vi.fn()
    let resolve!: (value: Document) => void
    vi.mocked(api.upload).mockReturnValue(new Promise(done => { resolve = done }))
    const { container, unmount } = render(<Upload onDocument={onDocument}/>)
    await user.upload(container.querySelector('input[type=file]')!, new File(['content'], 'source.txt', { type: 'text/plain' }))
    unmount()
    await act(async () => { resolve(document) })
    expect(onDocument).not.toHaveBeenCalled()
  })
  it('keeps generated course membership fixed while allowing title edits', async () => {
    const user = userEvent.setup()
    render(<Outline course={course} document={document} config={config} onCourse={vi.fn()} onGenerate={vi.fn()} onBack={vi.fn()} busy={false}/>)
    await user.click(screen.getByRole('button', { name: 'Edit outline' }))
    expect(screen.getByLabelText('Module 1 assignments')).toBeDisabled()
    expect(screen.getByLabelText('Module 2 quizzes')).toBeDisabled()
    expect(screen.getByLabelText('Module 1 title')).toBeEnabled()
  })
  it('preserves previously selected OCR pages when adding another page', async () => {
    const user = userEvent.setup(), file = new File(['pdf'], 'scan.pdf', { type: 'application/pdf' })
    vi.mocked(api.upload).mockResolvedValue(document)
    render(<DocumentReview document={{ ...document, format: 'pdf', ocr_pages: [1], needs_ocr_pages: [2] }} file={file} ocr={{ available: true, max_pages: 5, language: 'eng' }} onDocument={vi.fn()} onContinue={vi.fn()} onBack={vi.fn()}/>)
    expect(screen.getByRole('checkbox', { name: 'Page 1' })).toBeChecked()
    await user.click(screen.getByRole('checkbox', { name: 'Page 2' }))
    await user.click(screen.getByRole('button', { name: 'Read selected pages with OCR' }))
    expect(api.upload).toHaveBeenCalledWith(file, [1, 2])
  })
})
