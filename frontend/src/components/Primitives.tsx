import { AlertCircle, ArrowLeft, Check, LoaderCircle, LockKeyhole, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'warning' | 'error' | 'success' }) { return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : undefined}><AlertCircle size={19}/><div>{children}</div></div> }
export function Busy({ label = 'Working…' }: { label?: string }) { return <span className="busy"><LoaderCircle className="spin" size={18}/>{label}</span> }
export function Back({ onClick, label = 'Back' }: { onClick: () => void; label?: string }) { return <button className="text-button back-button" onClick={onClick}><ArrowLeft size={16}/>{label}</button> }
export function PrivacyLine() { return <div className="privacy-line"><LockKeyhole size={19}/><p>Your materials stay on your device. Only selected excerpts go to OpenAI when you choose to generate.</p></div> }
export function Steps({ current }: { current: number }) { return <ol className="steps">{['Add your material', 'Shape your course', 'Make it yours'].map((label, i) => <li key={label} className={i === current ? 'current' : i < current ? 'done' : ''}><span>{i < current ? <Check size={18}/> : `0${i + 1}`}</span><span>{label}</span></li>)}</ol> }
export function Modal({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => { dialog?.close() } }, [])
  return <dialog ref={ref} className={`modal ${wide ? 'modal-wide' : ''}`} onCancel={event => { event.preventDefault(); onClose() }} aria-label={title}><header className="modal-header"><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20}/></button></header>{children}</dialog>
}
