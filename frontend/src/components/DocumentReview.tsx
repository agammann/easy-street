import { ArrowRight, FileText } from 'lucide-react'
import type { Document } from '../types'
import { Back, Notice, Steps } from './Primitives'
import { useState } from 'react'

export function DocumentReview({ document, onContinue, onBack }: { document: Document; onContinue: () => void; onBack: () => void }) {
  const [index, setIndex] = useState(0)
  const passage = document.passages[index]
  return <section className="flow-page"><Back onClick={onBack} label="Choose another source"/><Steps current={0}/><div className="page-heading"><h1>Meet your material.</h1><p>Check what we could read before shaping your course.</p></div><div className="source-summary"><FileText size={24}/><div><strong>{document.filename}</strong><span>{document.passages.length} source passages · extracted on this device{document.cached ? ' · cached extraction' : ''}</span></div>{document.is_sample ? <span className="badge">Original sample</span> : null}</div>
    {document.warnings.map((warning, i) => <Notice tone="warning" key={i}>{warning}</Notice>)}
    <Notice>Text extraction cannot reliably interpret every table, image, or equation. Compare this preview with your original and use a readable chapter. OCR is not included in this release.</Notice>
    <div className="extraction-layout"><nav className="passage-list" aria-label="Extracted passages">{document.passages.map((item, i) => <button key={item.id} onClick={() => setIndex(i)} aria-current={i === index ? 'true' : undefined}><small>{item.location}</small><span>{item.heading || item.text.slice(0, 68)}</span></button>)}</nav><article className="passage-preview">{passage ? <><span className="eyebrow">{passage.location}</span><h2>{passage.heading || 'Extracted passage'}</h2><p className="preserve-lines">{passage.text}</p><small className="source-id">Source ID: {passage.id}</small></> : <Notice tone="error">No readable passages were found. Choose another chapter.</Notice>}</article></div>
    <div className="form-footer"><p>Use material you have permission to process.</p><button className="button primary" disabled={!passage} onClick={onContinue}>Looks good. Shape my course<ArrowRight size={18}/></button></div>
  </section>
}
