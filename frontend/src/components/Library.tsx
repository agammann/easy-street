import { Archive, ArrowRight, BookOpen, FileText, FolderOpen, Plus, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import { api, errorMessage } from '../api'
import type { Course, DocumentSummary } from '../types'
import { Busy, Notice } from './Primitives'
import { useMounted } from '../useMounted'

export function CourseLibrary({ courses, onOpen, onNew, onCourse }: { courses: Course[]; onOpen: (course: Course) => void; onNew: () => void; onCourse?: (course: Course) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const mounted = useMounted()
  const [archived, setArchived] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const visible = courses.filter(course => !!course.archived === archived)
  const archivedCount = courses.filter(course => course.archived).length
  async function importBackup(file?: File) {
    if (!file || busy) return
    if (!/\.json$/i.test(file.name) || file.size > 15 * 1024 * 1024) { setError('Choose an Easy Street JSON backup up to 15 MB.'); return }
    setBusy(true); setError('')
    try { const course = await api.importCourse(file); if (mounted.current) { onCourse?.(course); setArchived(false); onOpen(course) } } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  async function archive(course: Course) {
    setBusy(true); setError('')
    try { onCourse?.(await api.archiveCourse(course.id, !course.archived)) } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <section className="flow-page"><div className="list-heading"><div><h1>Your curiosity, collected.</h1><p>Pick up where you left off. Every course is saved on this device.</p></div><div className="library-actions"><input type="file" aria-label="Import course backup" ref={input} accept=".json,application/json" hidden onChange={event => { void importBackup(event.target.files?.[0]); event.target.value = '' }}/><button className="button secondary" disabled={busy} onClick={() => input.current?.click()}><Upload size={17}/>Import JSON backup</button><button className="button primary" disabled={busy} onClick={onNew}><Plus size={18}/>New course</button></div></div>
    <div className="library-filters"><div className="segmented" aria-label="Course library filter"><button className={!archived ? 'selected' : ''} onClick={() => setArchived(false)} aria-pressed={!archived}>Active ({courses.length - archivedCount})</button><button className={archived ? 'selected' : ''} onClick={() => setArchived(true)} aria-pressed={archived}>Archived ({archivedCount})</button></div><p className="field-help">Backups preserve course content. Keep your original source file separately.</p></div>
    {error ? <Notice tone="error">{error}</Notice> : null}{busy ? <p role="status"><Busy label="Updating your library…"/></p> : null}
    <div className="saved-list">{visible.map(course => <div className="saved-course-row" key={course.id}><button className="saved-row" onClick={() => onOpen(course)} disabled={busy}><span className="file-icon"><BookOpen/></span><span className="saved-copy"><strong>{course.title}</strong><small>{course.mode === 'demo' ? 'Offline demo · ' : ''}{course.status.replace(/_/g, ' ')} · {course.options.modules} module{course.options.modules === 1 ? '' : 's'} · {course.sections.length} sections · Updated {new Date(course.updated_at).toLocaleDateString()}{course.source_missing ? ' · Source needed' : ''}</small></span><ArrowRight size={20}/></button><button className="archive-button text-button" disabled={busy} onClick={() => void archive(course)} title={course.archived ? 'Return to active courses' : 'Move to archived courses'}>{course.archived ? <FolderOpen size={17}/> : <Archive size={17}/>}<span>{course.archived ? 'Unarchive' : 'Archive'}</span></button></div>)}</div>
    {!visible.length ? <div className="empty-state"><BookOpen size={38}/><h2>{archived ? 'Room to keep the old chapters.' : 'A fresh page.'}</h2><p>{archived ? 'Archived courses stay saved and can be brought back at any time.' : 'Start with your own reading or import a course backup.'}</p>{!archived ? <button className="button primary" onClick={onNew}>Create your first course</button> : null}</div> : null}
  </section>
}
export function SourceLibrary({ documents, onOpen, onNew }: { documents: DocumentSummary[]; onOpen: (id: string) => void; onNew: () => void }) {
  return <section className="flow-page"><div className="list-heading"><div><h1>Good ideas live here.</h1><p>Your source material, extracted and stored locally.</p></div><button className="button primary" onClick={onNew}><Plus size={18}/>Add material</button></div><div className="saved-list">{documents.map(document => <button className="saved-row" key={document.id} onClick={() => onOpen(document.id)}><span className="file-icon"><FileText/></span><span className="saved-copy"><strong>{document.filename}</strong><small>{document.format.toUpperCase()}{document.is_sample ? ' · Original sample' : ''} · Added {new Date(document.created_at).toLocaleDateString()}{document.warnings.length ? ` · ${document.warnings.length} extraction warning(s)` : ''}</small></span><span className="row-action">Review source<ArrowRight size={18}/></span></button>)}</div>{!documents.length ? <div className="empty-state"><FileText size={38}/><h2>Make a little space for learning.</h2><p>Add a PDF, DOCX, or text file to get started.</p><button className="button primary" onClick={onNew}>Choose a source</button></div> : null}</section>
}
