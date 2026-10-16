import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { api, errorMessage } from '../api'
import type { Config, Course, Document } from '../types'
import { Back, Busy, Notice, Steps } from './Primitives'

export function CourseOptions({ document, config, onCourse, onBack }: { document: Document; config: Config | null; onCourse: (course: Course) => void; onBack: () => void }) {
  const [title, setTitle] = useState(document.filename.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' '))
  const [difficulty, setDifficulty] = useState('introductory')
  const [modules, setModules] = useState(1)
  const [assignments, setAssignments] = useState(1)
  const [quizzes, setQuizzes] = useState(1)
  const [questions, setQuestions] = useState(3)
  const [mode, setMode] = useState<'openai' | 'demo'>(document.is_sample ? 'demo' : 'openai')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const maxModules = Math.min(6, document.passages.length)
  const maxAssessments = Math.min(6, modules * 2)
  const validCounts = Number.isInteger(modules) && modules >= 1 && modules <= maxModules && [assignments, quizzes].every(value => Number.isInteger(value) && value >= 0 && value <= maxAssessments) && Number.isInteger(questions) && questions >= 1 && questions <= 5
  function changeModules(value: number) { setModules(value); if (value >= 1) { setAssignments(current => Math.min(current, value * 2)); setQuizzes(current => Math.min(current, value * 2)) } }
  async function submit(event: React.FormEvent) { event.preventDefault(); if (!validCounts) return; setBusy(true); setError(''); try { onCourse(await api.createCourse({ document_id: document.id, title: title.trim(), difficulty, modules, assignments, quizzes, questions_per_quiz: questions, mode })) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  return <section className="flow-page"><Back onClick={onBack} label="Review source"/><Steps current={1}/><div className="page-heading"><h1>Make room for curiosity.</h1><p>Choose your course shape. You’ll review every module and its source coverage next.</p></div>
    <form onSubmit={submit} className="options-form"><div className="form-main">
      <label>Course title<input required maxLength={150} value={title} onChange={e => setTitle(e.target.value)}/></label>
      <label>Intended difficulty<select value={difficulty} onChange={e => setDifficulty(e.target.value)}><option value="introductory">Introductory — build a foundation</option><option value="intermediate">Intermediate — connect the ideas</option><option value="advanced">Advanced — examine in depth</option></select></label>
      <fieldset><legend>Course-wide totals</legend><div className="count-fields"><label>Learning modules<input type="number" min={1} max={maxModules} required value={modules} onChange={e => changeModules(Number(e.target.value))}/></label><label>Written assignments<input type="number" min={0} max={maxAssessments} required value={assignments} onChange={e => setAssignments(Number(e.target.value))}/></label><label>Quizzes<input type="number" min={0} max={maxAssessments} required value={quizzes} onChange={e => setQuizzes(Number(e.target.value))}/></label></div><p className="field-help">Up to 6 modules, 6 assignments, and 6 quizzes. Each module can hold up to 2 of each assessment. These are totals for the whole course. This source supports up to {maxModules} modules.</p></fieldset>
      <label>Questions per quiz<input type="number" min={1} max={5} required disabled={!quizzes} value={questions} onChange={e => setQuestions(Number(e.target.value))}/></label>
      <fieldset><legend>Generation mode</legend><label className="radio-option"><input type="radio" name="mode" checked={mode === 'openai'} onChange={() => setMode('openai')}/><span><strong>OpenAI with your own API key</strong><small>Software is free. Your provider charges your account for usage.</small></span></label>{document.is_sample ? <label className="radio-option"><input type="radio" name="mode" checked={mode === 'demo'} onChange={() => setMode('demo')}/><span><strong>Offline demo</strong><small>Prewritten sample content. No provider call and no cost.</small></span></label> : null}</fieldset>
      {mode === 'openai' && !config?.key_configured ? <Notice tone="warning">Your backend API key is not configured. You can prepare the outline now; add your own key before generation. See Settings.</Notice> : null}
    </div><aside className="course-shape"><h2>A little structure.<br/>A lot to discover.</h2><p>{modules || 0} module{modules !== 1 ? 's' : ''}, shaped around your material.</p><ul><li>Learning objectives & introductions</li><li>Source-linked readings & notes</li><li>{assignments || 0} written assignment{assignments !== 1 ? 's' : ''} with rubrics</li><li>{quizzes || 0} quiz{quizzes !== 1 ? 'zes' : ''} · {quizzes * questions || 0} questions total</li><li>A syllabus and separate answer key</li></ul><p className="field-help">Structure, prompts, and rubrics are proposals for you to review.</p></aside>
    <div className="form-footer">{error ? <Notice tone="error">{error}</Notice> : <p>Creating the outline is local and free.</p>}<button className="button primary" disabled={busy || !title.trim() || !validCounts || document.insufficient_text}>{busy ? <Busy label="Preparing outline…"/> : <>Preview my outline<ArrowRight size={18}/></>}</button></div></form>
  </section>
}
