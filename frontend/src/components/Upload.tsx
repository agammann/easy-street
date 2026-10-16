import { ArrowRight, BookOpen } from 'lucide-react'
import { useRef, useState } from 'react'
import { api, errorMessage } from '../api'
import type { Document } from '../types'
import { Busy, Notice, Steps } from './Primitives'

export function Upload({ onDocument }: { onDocument: (document: Document) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  async function upload(file?: File) {
    if (!file || busy) return
    if (!/\.(pdf|txt)$/i.test(file.name)) { setError('Choose a readable PDF or a UTF-8 text file.'); return }
    if (file.size > 15 * 1024 * 1024) { setError('This file is larger than 15 MB. Please choose one smaller chapter.'); return }
    setError(''); setBusy(true)
    try { onDocument(await api.upload(file)) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  async function sample() { setBusy(true); setError(''); try { onDocument(await api.sample()) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  return <>
    <section className="hero"><div className="hero-copy"><h1>Big ideas.<br/><em>Your own way.</em></h1><p>Turn your reading into a course<br className="desktop-break"/> you can actually make your own.</p></div><div className="hero-art"><img src="/learning-road.png" alt="An open book becomes a winding road through a bright landscape"/></div></section>
    <section className="start-section"><Steps current={0}/>
      <div className="upload-grid"><div className={`upload-zone ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); void upload(event.dataTransfer.files[0]) }} aria-busy={busy}><div className="upload-icon"><BookOpen size={58} strokeWidth={1.5}/></div><h2>Every great course starts with a page.</h2><p>Drop in a chapter, article, or a few good notes.</p><input ref={input} type="file" accept=".pdf,.txt,application/pdf,text/plain" hidden onChange={event => { void upload(event.target.files?.[0]); event.target.value = '' }}/><button className="button primary" disabled={busy} onClick={() => input.current?.click()}>{busy ? <Busy label="Reading locally…"/> : 'Choose a file'}</button><small>PDF or TXT · up to 15 MB</small><div className="sample-action"><span>Just looking around?</span> <button className="text-button" onClick={() => void sample()} disabled={busy}>Try the sample chapter<ArrowRight size={19}/></button><span className="sample-note">Original sample · free offline demo available</span></div></div>
      <aside className="benefits-panel"><h2>Small steps.<br/>Real understanding.</h2><ol><li><span>1</span><div><h3>Read with a plan</h3><p>Turn what you’re reading into a clear, structured outline.</p></div></li><li><span>2</span><div><h3>Put it into practice</h3><p>Practice with a written assignment and a quiz.</p></div></li><li><span>3</span><div><h3>Make it yours</h3><p>Edit, rearrange, and add your perspective. A course that fits you.</p></div></li></ol></aside></div>
      {error ? <Notice tone="error">{error}</Notice> : null}
    </section>
  </>
}
