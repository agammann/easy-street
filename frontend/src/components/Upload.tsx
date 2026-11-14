import { ArrowRight, BookOpen } from 'lucide-react'
import { useRef, useState } from 'react'
import { api, errorMessage } from '../api'
import type { Config, Course, Document, Job } from '../types'
import { useMounted } from '../useMounted'
import { maxUploadMiB } from '../providers'
import { Busy, Notice, Steps } from './Primitives'

export function Upload({ onDocument, config, onSampleCourse }: { onDocument: (document: Document, file?: File) => void; config?: Config | null; onSampleCourse?: (result: { course: Course; document: Document; job: Job }) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const sampleRequest = useRef<string | null>(null)
  const mounted = useMounted()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const judging = config?.hosting_mode === 'judging'
  const maxUpload = maxUploadMiB(config)
  async function upload(file?: File) {
    if (!file || busy) return
    if (!/\.(pdf|txt|docx)$/i.test(file.name)) { setError('Choose a PDF, DOCX, or UTF-8 text file.'); return }
    if (file.size > maxUpload * 1024 * 1024) { setError(`This file is larger than ${maxUpload} MB. Please choose one smaller chapter.`); return }
    setError(''); setBusy(true)
    try { const document = await api.upload(file); if (mounted.current) onDocument(document, file) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  async function sample() { setBusy(true); setError(''); try { const document = await api.sample(); if (mounted.current) onDocument(document) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  async function sampleCourse() {
    if (busy || !onSampleCourse) return
    setBusy(true); setError(''); sampleRequest.current ||= crypto.randomUUID()
    try { const result = await api.sampleCourse(sampleRequest.current); if (mounted.current) onSampleCourse(result); sampleRequest.current = null } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <>
    <section className="hero"><div className="hero-copy"><h1>Big ideas.<br/><em>Your own way.</em></h1><p>Turn your reading into a course<br className="desktop-break"/> you can actually make your own.</p></div><div className="hero-art"><img src="/learning-road.png" alt="An open book becomes a winding road through a bright landscape"/></div></section>
    <section className="start-section"><Steps current={0}/>
      <div className="upload-grid"><div className={`upload-zone ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); void upload(event.dataTransfer.files[0]) }} aria-busy={busy}><div className="upload-icon"><BookOpen size={58} strokeWidth={1.5}/></div><h2>Every great course starts with a page.</h2><p>Drop in a chapter, article, or a few good notes.</p><input ref={input} type="file" accept=".pdf,.docx,.txt,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden onChange={event => { void upload(event.target.files?.[0]); event.target.value = '' }}/><button className="button primary" disabled={busy} onClick={() => input.current?.click()}>{busy ? <Busy label={judging ? "Reading your temporary upload…" : "Reading locally…"}/> : 'Choose a file'}</button><small>PDF, DOCX, or TXT · up to {maxUpload} MB</small><div className="sample-action"><span>Just looking around?</span> <button className="text-button" onClick={() => void sample()} disabled={busy}>Try the sample chapter<ArrowRight size={19}/></button><span className="sample-note">Original sample · <a href="/sample-license.txt" target="_blank" rel="noreferrer">sample license</a> · free offline demo available</span>{judging && onSampleCourse ? <div className="judge-sample"><p>Generate a complete sample course in one click. By continuing, you approve sending excerpts of the original garden chapter to Nebius Token Factory. The operator funds this bounded demo.</p><button className="button secondary" disabled={busy} onClick={() => void sampleCourse()}>{busy ? <Busy label="Starting the sample…"/> : <>Generate sample with Nebius<ArrowRight size={17}/></>}</button><small>1 module · 1 assignment · 1 quiz · 3 questions. Review all content against its source.</small></div> : null}</div></div>
      <aside className="benefits-panel"><h2>Small steps.<br/>Real understanding.</h2><ol><li><span>1</span><div><h3>Read with a plan</h3><p>Turn what you’re reading into a clear, structured outline.</p></div></li><li><span>2</span><div><h3>Put it into practice</h3><p>Practice with assignments and quizzes that fit your course.</p></div></li><li><span>3</span><div><h3>Make it yours</h3><p>Edit, rearrange, and add your perspective. A course that fits you.</p></div></li></ol></aside></div>
      {error ? <Notice tone="error">{error}</Notice> : null}
    </section>
  </>
}
