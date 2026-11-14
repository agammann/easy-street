import { ArrowRight, FileText } from 'lucide-react'
import type { Document, OcrCapability } from '../types'
import { Back, Busy, Notice, Steps } from './Primitives'
import { useRef, useState } from 'react'
import { api, errorMessage } from '../api'
import { useMounted } from '../useMounted'

export function DocumentReview({ document, file, ocr, onDocument, onContinue, onBack, judging = false, maxUpload = 15 }: { maxUpload?: number; judging?: boolean; document: Document; file?: File; ocr?: OcrCapability; onDocument?: (document: Document, file?: File) => void; onContinue: () => void; onBack: () => void }) {
  const [index, setIndex] = useState(0)
  const mounted = useMounted()
  const [pages, setPages] = useState<number[]>(document.ocr_pages ?? [])
  const [localFile, setLocalFile] = useState(file)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const passage = document.passages[Math.min(index, Math.max(0, document.passages.length - 1))]
  const maxPages = ocr?.max_pages ?? 5
  const ocrCandidates = [...new Set([...(document.needs_ocr_pages ?? []), ...(document.ocr_pages ?? [])])].sort((a, b) => a - b)
  async function chooseFile(next?: File) {
    if (!next) return
    setError('')
    if (next.size > maxUpload * 1024 * 1024) { setError(`Choose the original PDF, up to ${maxUpload} MB.`); return }
    try {
      const bytes = await crypto.subtle.digest('SHA-256', await next.arrayBuffer())
      const hash = Array.from(new Uint8Array(bytes), value => value.toString(16).padStart(2, '0')).join('')
      if (hash !== document.sha256) { setError('This file does not match the original source. Choose the same PDF used for this extraction.'); return }
      setLocalFile(next)
    } catch { setError('Could not read this file. Choose the original PDF again.') }
  }
  async function runOcr() {
    if (!localFile || !pages.length || !onDocument) return
    setBusy(true); setError('')
    try { const updated = await api.upload(localFile, pages); if (mounted.current) onDocument(updated, localFile); setPages(updated.ocr_pages ?? []); setIndex(0) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <section className="flow-page"><Back onClick={onBack} label="Choose another source"/><Steps current={0}/><div className="page-heading"><h1>Meet your material.</h1><p>Check what we could read before shaping your course.</p></div><div className="source-summary"><FileText size={24}/><div><strong>{document.filename}</strong><span>{document.passages.length} source passages · {judging ? "extracted on the demo server" : "extracted on this device"}{document.cached ? ' · cached extraction' : ''}</span></div>{document.is_sample ? <span className="badge">Original sample</span> : null}</div>
    {document.warnings.map((warning, i) => <Notice tone="warning" key={i}>{warning}</Notice>)}
    <Notice>Text extraction cannot reliably interpret every table, image, or equation. Compare this preview with your original before continuing.</Notice>
    {document.needs_ocr_pages?.length ? <section className="ocr-panel"><div><span className="eyebrow">OPTIONAL OCR</span><h2>Give scanned pages a second look.</h2><p>These PDF pages have little or no readable text. Choose up to {maxPages} pages to recognize English text {judging ? "on the demo server" : "on this device"}. OCR can make mistakes; check the new preview.</p></div>
      {ocr?.available ? <><div className="ocr-page-options">{ocrCandidates.map(page => <label className="checkbox-label" key={page}><input type="checkbox" checked={pages.includes(page)} disabled={busy || (!pages.includes(page) && pages.length >= maxPages)} onChange={event => setPages(current => event.target.checked ? [...current, page].sort((a, b) => a - b) : current.filter(value => value !== page))}/><span>Page {page}</span></label>)}</div><p className="field-help">{pages.length} / {maxPages} pages selected. Keep previous selections to retain their recognized text. No provider call or API cost.</p>{!localFile ? <><input type="file" accept=".pdf,application/pdf" ref={fileInput} hidden onChange={event => { void chooseFile(event.target.files?.[0]); event.target.value = '' }}/><button className="button secondary" disabled={busy} onClick={() => fileInput.current?.click()}>Choose original PDF for OCR</button></> : <button className="button secondary" disabled={busy || !pages.length} onClick={() => void runOcr()}>{busy ? <Busy label="Recognizing selected pages…"/> : 'Read selected pages with OCR'}</button>}</> : <Notice tone="warning">{ocr?.reason || 'Local OCR tools are not installed.'} {judging ? "Choose a readable source, or contact the operator about OCR availability." : "See the README’s optional OCR setup, restart the app, and reopen this source."}</Notice>}
      {error ? <Notice tone="error">{error}</Notice> : null}
    </section> : null}
    <div className="extraction-layout"><nav className="passage-list" aria-label="Extracted passages">{document.passages.map((item, i) => <button key={item.id} onClick={() => setIndex(i)} aria-current={i === index ? 'true' : undefined}><small>{item.location}</small><span>{item.heading || item.text.slice(0, 68)}</span></button>)}</nav><article className="passage-preview">{passage ? <><span className="eyebrow">{passage.location}</span><h2>{passage.heading || 'Extracted passage'}</h2><p className="preserve-lines">{passage.text}</p><small className="source-id">Source ID: {passage.id}</small></> : <Notice tone="warning">No readable passages were found. Use OCR for scanned pages, or choose a readable source.</Notice>}</article></div>
    <div className="form-footer"><p>Use material you have permission to process.</p><button className="button primary" disabled={!passage || document.insufficient_text || busy} onClick={onContinue}>Looks good. Shape my course<ArrowRight size={18}/></button></div>
  </section>
}
