import { useRef, useState } from 'react'
import { api, errorMessage } from '../api'
import type { Course, Document } from '../types'
import { Busy, Notice } from './Primitives'
import { useMounted } from '../useMounted'

export function SourceRecovery({ course, document, disabled, onAttached }: { course: Course; document: Document | null; disabled: boolean; onAttached: (course: Course, document: Document) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const mounted = useMounted()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function restore(file?: File) {
    if (!file || busy) return
    if (file.size > 15 * 1024 * 1024) { setError('Choose the original source file, up to 15 MB.'); return }
    setBusy(true); setError('')
    try { const updated = await api.reattachSource(course.id, file); const source = await api.document(updated.document_id); if (mounted.current) onAttached(updated, source) } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <div className="source-recovery"><Notice tone="warning"><strong>Bring your source back.</strong><p>This backup has course content but no original source passages. You can edit and export now. Restore {document?.filename || 'the original file'} to inspect full evidence and generate content. Only a file matching the original will be accepted.</p><input type="file" ref={input} aria-label="Restore original source" accept=".pdf,.docx,.txt" hidden onChange={event => { void restore(event.target.files?.[0]); event.target.value = '' }}/><button className="button secondary" disabled={busy || disabled} onClick={() => input.current?.click()}>{busy ? <Busy label="Restoring source…"/> : 'Restore original source'}</button></Notice>{error ? <Notice tone="error">{error}</Notice> : null}</div>
}
