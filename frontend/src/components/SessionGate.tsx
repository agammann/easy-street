import { useEffect, useState, type ReactNode } from 'react'
import { BookOpen, LockKeyhole, Trash2 } from 'lucide-react'
import { api, errorMessage, setCsrfToken } from '../api'
import type { Session } from '../types'
import { Busy, Modal, Notice } from './Primitives'

function clearRememberedWorkspace() {
  try {
    localStorage.removeItem('easy-street-workspace-v1')
    for (const key of Object.keys(localStorage)) if (key.startsWith('easy-street-generation-v1:')) localStorage.removeItem(key)
  } catch { /* Browser storage is optional. */ }
}

export function SessionGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [accessCode, setAccessCode] = useState('')
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  function accept(next: Session) {
    setCsrfToken(next.mode === 'judging' && next.authenticated ? next.csrf_token : undefined)
    setSession(next)
  }
  async function reload() {
    setLoading(true); setError('')
    try { accept(await api.session()) } catch (e) { setError(errorMessage(e)) } finally { setLoading(false) }
  }
  useEffect(() => {
    let active = true
    api.session().then(next => { if (active) accept(next) }).catch(e => { if (active) setError(errorMessage(e)) }).finally(() => { if (active) setLoading(false) })
    const expired = () => { setCsrfToken(); clearRememberedWorkspace(); setSession({ mode: 'judging', authenticated: false }); setConfirmDelete(false); setError('Your temporary session has ended. Enter the judging access code to open a new workspace.') }
    window.addEventListener('easy-street-session-expired', expired)
    return () => { active = false; setCsrfToken(); window.removeEventListener('easy-street-session-expired', expired) }
  }, [])
  async function signIn(event: React.FormEvent) {
    event.preventDefault(); if (busy || !accessCode.trim()) return
    setBusy(true); setError('')
    try { const next = await api.signIn(accessCode.trim()); clearRememberedWorkspace(); accept(next); setAccessCode('') } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  async function removeWorkspace() {
    setBusy(true); setError('')
    try { await api.deleteSession(); clearRememberedWorkspace(); accept({ mode: 'judging', authenticated: false }); setConfirmDelete(false) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  if (loading) return <main className="access-page"><Busy label="Opening Easy Street…"/></main>
  if (session?.mode === 'local') return children
  if (session?.authenticated && session.csrf_token) return <><aside className="session-banner" aria-label="Temporary judging workspace"><div><strong><LockKeyhole size={17}/>Your private judging workspace</strong><p>Documents and results are stored temporarily on this server and are isolated from other visitors. {session.expires_at ? `This workspace expires ${new Date(session.expires_at).toLocaleString()}.` : `Temporary files expire after ${session.retention_hours ?? 24} hours.`} Download any exports you want to keep.</p></div><button className="text-button" onClick={() => { setError(''); setConfirmDelete(true) }}><Trash2 size={16}/>Delete my workspace</button></aside>{children}{confirmDelete ? <Modal title="Delete your temporary workspace?" onClose={() => { if (!busy) setConfirmDelete(false) }}><p>This permanently deletes this session’s uploaded documents, courses, and saved results from the server, then signs you out. Download anything you want to keep first.</p><p>An active generation must finish or be cancelled before deletion can complete.</p>{error ? <Notice tone="error">{error}</Notice> : null}<div className="dialog-actions"><button className="button secondary" disabled={busy} onClick={() => setConfirmDelete(false)}>Keep my workspace</button><button className="button danger" disabled={busy} onClick={() => void removeWorkspace()}>{busy ? <Busy label="Deleting…"/> : 'Delete files & sign out'}</button></div></Modal> : null}</>
  return <main className="access-page"><div className="access-card"><span className="access-mark"><BookOpen size={40}/></span><span className="eyebrow">EASY STREET · JUDGING DEMO</span><h1>A chapter.<br/>A course.<br/><em>Your own way.</em></h1><p>Try real course generation with Nebius Token Factory and NVIDIA Nemotron. The operator funds this limited demo; you do not need an API key.</p><form onSubmit={signIn}><label>Judging access code<input type="password" autoComplete="off" required maxLength={200} value={accessCode} onChange={event => setAccessCode(event.target.value)} disabled={busy}/></label><p className="field-help">Use the code in the Devpost judge testing instructions. For access help, contact the project owner through the submission.</p><button className="button primary" disabled={busy || !accessCode.trim() || !session}>{busy ? <Busy label="Opening your workspace…"/> : 'Open my private workspace'}</button></form>{error ? <Notice tone="error">{error}</Notice> : null}{!session || (session.authenticated && !session.csrf_token) ? <button className="text-button" disabled={busy} onClick={() => void reload()}>Retry connection</button> : null}<p className="field-help">Your uploads and courses stay in an isolated temporary server workspace, retained for up to {session?.retention_hours ?? 24} hours. Only excerpts you approve are sent to Nebius. <a href="/sample-license.txt" target="_blank" rel="noreferrer">Original sample chapter license</a></p></div><div className="access-art"><img src="/learning-road.png" alt="An open book becomes a winding road through a bright landscape"/></div></main>
}
