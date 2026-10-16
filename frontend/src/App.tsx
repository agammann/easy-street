import { useCallback, useEffect, useState } from 'react'
import { api, errorMessage } from './api'
import type { Config, Course, Document, DocumentSummary, Job, Step, View } from './types'
import { Shell } from './components/Shell'
import { Upload } from './components/Upload'
import { DocumentReview } from './components/DocumentReview'
import { CourseOptions } from './components/CourseOptions'
import { Outline } from './components/Outline'
import { Generation } from './components/Generation'
import { Editor } from './components/Editor'
import { CourseLibrary, SourceLibrary } from './components/Library'
import { Settings } from './components/Settings'
import { Busy, Notice } from './components/Primitives'

const sessionKey = 'easy-street-workspace-v1'
function remember(courseId?: string, jobId?: string) { try { localStorage.setItem(sessionKey, JSON.stringify({ courseId, jobId })) } catch { /* Storage is optional; server data persists. */ } }
export default function App() {
  const [view, setView] = useState<View>('courses')
  const [step, setStep] = useState<Step>('upload')
  const [list, setList] = useState(false)
  const [config, setConfig] = useState<Config | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [document, setDocument] = useState<Document | null>(null)
  const [course, setCourse] = useState<Course | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dirty, setDirty] = useState(false)
  const [navigationBlocked, setNavigationBlocked] = useState(false)
  useEffect(() => { if (!dirty) setNavigationBlocked(false) }, [dirty])
  const refresh = useCallback(async () => { const [nextConfig, nextCourses, nextDocuments] = await Promise.all([api.config(), api.courses(), api.documents()]); setConfig(nextConfig); setCourses(nextCourses); setDocuments(nextDocuments) }, [])
  useEffect(() => {
    let active = true
    async function start() { try { await refresh(); let saved: { courseId?: string; jobId?: string } = {}; try { saved = JSON.parse(localStorage.getItem(sessionKey) || '{}') } catch { /* Ignore invalid UI state. */ } if (saved.courseId) { try { const current = await api.course(saved.courseId); const source = await api.document(current.document_id); if (!active) return; setCourse(current); setDocument(source); setStep(current.sections.length ? 'editor' : 'outline'); if (saved.jobId) { const existing = await api.job(saved.jobId); if (!active) return; setJob(existing); if (['queued', 'running', 'interrupted', 'uncertain'].includes(existing.status)) setStep('generation') } } catch { remember() } } } catch(e) { if (active) setError(errorMessage(e)) } finally { if (active) setLoading(false) } }
    void start(); return () => { active = false }
  }, [refresh])
  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return
    let active = true
    let inFlight = false
    const timer = window.setInterval(async () => {
      if (inFlight) return
      inFlight = true
      try {
        const next = await api.job(job.id)
        if (!active) return
        if (!['queued', 'running'].includes(next.status)) {
          const updated = await api.course(next.course_id)
          if (!active) return
          setCourse(current => current?.id === updated.id ? updated : current)
          setJob(next)
          void refresh().catch(() => undefined)
        } else {
          setJob(next)
        }
      } catch(e) { if (active) setError(errorMessage(e)) }
      finally { inFlight = false }
    }, 1200)
    return () => { active = false; window.clearInterval(timer) }
  }, [job?.id, job?.status, refresh])
  const updateCourse = (updated: Course) => { setCourse(updated); setCourses(current => [updated, ...current.filter(item => item.id !== updated.id)]); remember(updated.id, job?.course_id === updated.id ? job.id : undefined) }
  function newCourse() { setCourse(null); setDocument(null); setJob(null); setStep('upload'); setView('courses'); setList(false); setError(''); remember() }
  function selectDocument(source: Document) { setDocument(source); setStep('preview'); setList(false); setView('courses'); setDocuments(current => [source, ...current.filter(item => item.id !== source.id)]) }
  async function openCourse(selected: Course) { setBusy(true); setError(''); try { const [current, source] = await Promise.all([api.course(selected.id), api.document(selected.document_id)]); setCourse(current); setDocument(source); setView('courses'); setList(false); if (job?.course_id === current.id && ['queued', 'running', 'interrupted', 'uncertain'].includes(job.status)) setStep('generation'); else setStep(current.sections.length ? 'editor' : 'outline'); remember(current.id, job?.course_id === current.id ? job.id : undefined) } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  async function openDocument(id: string) { setBusy(true); setError(''); try { selectDocument(await api.document(id)) } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  async function generate(sectionId?: string) { if (!course) return; setBusy(true); try { const next = await api.generate(course.id, sectionId); setJob(next); remember(course.id, next.id); setStep('generation'); void refresh().catch(() => undefined) } finally { setBusy(false) } }
  function navigate(next: View) { if (dirty) { setNavigationBlocked(true); return } setNavigationBlocked(false); setView(next); setError(''); if (next === 'courses') setList(courses.length > 0); void refresh().catch(e => setError(errorMessage(e))) }
  function backToCourses() { if (dirty) { setNavigationBlocked(true); return } setNavigationBlocked(false); setList(true); void refresh().catch(e => setError(errorMessage(e))) }
  const breadcrumb = view === 'settings' ? 'Provider & privacy' : view === 'library' ? 'Your materials' : list ? 'Saved courses' : course ? course.title : 'New course'
  return <Shell view={view} onView={navigate} breadcrumb={breadcrumb}>{navigationBlocked ? <div className="global-error"><Notice tone="error">Save or cancel your section edits before leaving the course.</Notice></div> : null}{error ? <div className="global-error"><Notice tone="error">{error}<button className="text-button" onClick={() => { setError(''); void refresh().catch(e => setError(errorMessage(e))) }}>Retry loading workspace</button></Notice></div> : null}{loading ? <div className="app-loading"><Busy label="Opening your local workspace…"/></div> : <>
    {view === 'library' ? <SourceLibrary documents={documents} onOpen={id => void openDocument(id)} onNew={newCourse}/> : null}
    {view === 'settings' ? <Settings config={config} onRefresh={refresh}/> : null}
    {view === 'courses' && list ? <CourseLibrary courses={courses} onOpen={selected => void openCourse(selected)} onNew={newCourse}/> : null}
    {view === 'courses' && !list ? <>{step === 'upload' ? <Upload onDocument={selectDocument}/> : null}{step === 'preview' && document ? <DocumentReview document={document} onBack={newCourse} onContinue={() => setStep('options')}/> : null}{step === 'options' && document ? <CourseOptions document={document} config={config} onBack={() => setStep('preview')} onCourse={created => { updateCourse(created); setStep('outline') }}/>: null}{step === 'outline' && course ? <Outline key={course.id} course={course} config={config} onCourse={updateCourse} busy={busy} onBack={backToCourses} onGenerate={() => generate()}/> : null}{step === 'generation' && job && course ? <Generation job={job} course={course} onJob={setJob} onOpen={() => setStep(course.sections.length ? 'editor' : 'outline')}/> : null}{step === 'editor' && course ? <Editor course={course} document={document} onCourse={updateCourse} onBack={backToCourses} onRegenerate={id => generate(id)} onDirty={setDirty}/> : null}</> : null}
    {busy && (list || view === 'library') ? <div className="loading-toast" role="status"><Busy label="Opening…"/></div> : null}
  </>}</Shell>
}
