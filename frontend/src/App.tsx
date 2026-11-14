import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errorMessage } from './api'
import { configuredProvider, maxUploadMiB } from './providers'
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
import { SourceRecovery } from './components/SourceRecovery'
import { Busy, Notice } from './components/Primitives'

const sessionKey = 'easy-street-workspace-v1'
function remember(courseId?: string, jobId?: string) { try { localStorage.setItem(sessionKey, JSON.stringify({ courseId, jobId })) } catch { /* Storage is optional; server data persists. */ } }
async function loadCourse(id: string) {
  const [course, job] = await Promise.all([api.course(id), api.courseJob(id)])
  const document = await api.document(course.document_id)
  return { course, document, job }
}
function isRecoverableJob(job: Job | null) {
  return job !== null && ['queued', 'running', 'interrupted', 'uncertain'].includes(job.status)
}
export default function App() {
  const navigationSequence = useRef(0)
  const [view, setView] = useState<View>('courses')
  const [step, setStep] = useState<Step>('upload')
  const [list, setList] = useState(false)
  const [config, setConfig] = useState<Config | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [sourceFile, setSourceFile] = useState<File | undefined>()
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
    const sequence = navigationSequence.current
    async function start() {
      try {
        await refresh()
        let savedId: string | undefined
        try {
          const saved: unknown = JSON.parse(localStorage.getItem(sessionKey) || '{}')
          if (saved && typeof saved === 'object' && 'courseId' in saved && typeof saved.courseId === 'string') savedId = saved.courseId
        } catch { /* Ignore invalid UI state. */ }
        if (savedId) {
          const loaded = await loadCourse(savedId)
          if (!active || sequence !== navigationSequence.current) return
          setCourse(loaded.course)
          setDocument(loaded.document)
          setJob(loaded.job)
          setStep(isRecoverableJob(loaded.job) ? 'generation' : loaded.course.sections.length ? 'editor' : 'outline')
          remember(loaded.course.id, loaded.job?.id)
        }
      } catch(e) { if (active) setError(errorMessage(e)) }
      finally { if (active) setLoading(false) }
    }
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
  function newCourse() { navigationSequence.current++; setBusy(false); setCourse(null); setDocument(null); setSourceFile(undefined); setJob(null); setStep('upload'); setView('courses'); setList(false); setError(''); remember() }
  function selectDocument(source: Document, file?: File) { setDocument(source); setSourceFile(file); setCourse(null); setJob(null); remember(); setStep('preview'); setList(false); setView('courses'); setDocuments(current => [source, ...current.filter(item => item.id !== source.id)]) }
  function selectSampleCourse(result: { course: Course; document: Document; job: Job }) {
    setCourse(result.course); setDocument(result.document); setSourceFile(undefined); setJob(result.job); setList(false); setView('courses'); setError('')
    setStep(result.job.status === 'complete' ? 'editor' : 'generation'); remember(result.course.id, result.job.id)
    void refresh().catch(e => setError(errorMessage(e)))
  }
  async function openCourse(selected: Course) {
    const sequence = ++navigationSequence.current
    setBusy(true); setError('')
    try {
      const loaded = await loadCourse(selected.id)
      if (sequence !== navigationSequence.current) return
      setCourse(loaded.course); setDocument(loaded.document); setJob(loaded.job); setView('courses'); setList(false)
      setStep(isRecoverableJob(loaded.job) ? 'generation' : loaded.course.sections.length ? 'editor' : 'outline')
      remember(loaded.course.id, loaded.job?.id)
    } catch(e) { if (sequence === navigationSequence.current) setError(errorMessage(e)) }
    finally { if (sequence === navigationSequence.current) setBusy(false) }
  }
  async function openDocument(id: string) {
    const sequence = ++navigationSequence.current
    setBusy(true); setError('')
    try { const source = await api.document(id); if (sequence === navigationSequence.current) selectDocument(source) }
    catch(e) { if (sequence === navigationSequence.current) setError(errorMessage(e)) }
    finally { if (sequence === navigationSequence.current) setBusy(false) }
  }
  async function generate(sectionId?: string) { if (!course) return; setBusy(true); try { const next = await api.generate(course.id, sectionId); setJob(next); remember(course.id, next.id); setStep('generation'); void refresh().catch(() => undefined) } finally { setBusy(false) } }
  async function acceptJob(next: Job) {
    const sequence = navigationSequence.current
    if (!['queued', 'running'].includes(next.status)) {
      const updated = await api.course(next.course_id)
      if (sequence !== navigationSequence.current) return
      setCourse(current => current?.id === updated.id ? updated : current)
      void refresh().catch(() => undefined)
    }
    setJob(next)
  }
  function navigate(next: View) { if (dirty) { setNavigationBlocked(true); return } navigationSequence.current++; setBusy(false); setNavigationBlocked(false); setView(next); setError(''); if (next === 'courses') setList(courses.length > 0); void refresh().catch(e => setError(errorMessage(e))) }
  function backToCourses() { if (dirty) { setNavigationBlocked(true); return } navigationSequence.current++; setBusy(false); setNavigationBlocked(false); setList(true); void refresh().catch(e => setError(errorMessage(e))) }
  const breadcrumb = view === 'settings' ? 'Provider & privacy' : view === 'library' ? 'Your materials' : list ? 'Saved courses' : course ? course.title : 'New course'
  return <Shell view={view} onView={navigate} breadcrumb={breadcrumb} config={config}>{navigationBlocked ? <div className="global-error"><Notice tone="error">Save or cancel your edits before leaving the course.</Notice></div> : null}{error ? <div className="global-error"><Notice tone="error">{error}<button className="text-button" onClick={() => { setError(''); void refresh().catch(e => setError(errorMessage(e))) }}>Retry loading workspace</button></Notice></div> : null}{loading ? <div className="app-loading"><Busy label="Opening your workspace…"/></div> : <>
    {view === 'library' ? <SourceLibrary judging={config?.hosting_mode === "judging"} documents={documents} onOpen={id => void openDocument(id)} onNew={newCourse}/> : null}
    {view === 'settings' ? <Settings config={config} onRefresh={refresh}/> : null}
    {view === 'courses' && list ? <CourseLibrary maxUpload={maxUploadMiB(config)} judging={config?.hosting_mode === "judging"} courses={courses} onOpen={selected => void openCourse(selected)} onNew={newCourse} onCourse={updated => setCourses(current => [updated, ...current.filter(item => item.id !== updated.id)])}/> : null}
    {view === 'courses' && !list ? <>{course?.source_missing && ['outline', 'editor'].includes(step) ? <SourceRecovery maxUpload={maxUploadMiB(config)} course={course} document={document} disabled={dirty} onAttached={(updated, source) => { updateCourse(updated); setDocument(source) }}/> : null}{step === 'upload' ? <Upload onDocument={selectDocument} config={config} onSampleCourse={selectSampleCourse}/> : null}{step === 'preview' && document ? <DocumentReview maxUpload={maxUploadMiB(config)} judging={config?.hosting_mode === "judging"} key={document.id} document={document} file={sourceFile} ocr={config?.ocr} onDocument={selectDocument} onBack={newCourse} onContinue={() => setStep('options')}/> : null}{step === 'options' && document ? <CourseOptions document={document} config={config} onBack={() => setStep('preview')} onCourse={created => { updateCourse(created); setStep('outline') }}/>: null}{step === 'outline' && course ? <Outline key={course.id} course={course} document={document} config={config} onApproved={() => setStep('editor')} onCourse={updateCourse} onDirty={setDirty} busy={busy} onBack={backToCourses} onGenerate={() => generate()}/> : null}{step === 'generation' && job && course ? <Generation judging={config?.hosting_mode === "judging"} job={job} course={course} onJob={acceptJob} onOpen={() => setStep(course.sections.length ? 'editor' : 'outline')}/> : null}{step === 'editor' && course ? <Editor course={course} onOutline={() => setStep('outline')} keyConfigured={configuredProvider(config, course.mode).key_configured} config={config} document={document} onCourse={updateCourse} onBack={backToCourses} onRegenerate={id => generate(id)} onDirty={setDirty}/> : null}</> : null}
    {busy && (list || view === 'library') ? <div className="loading-toast" role="status"><Busy label="Opening…"/></div> : null}
  </>}</Shell>
}
