import { BookOpen, Folder, Settings, LockKeyhole } from 'lucide-react'
import type { ReactNode } from 'react'
import type { View } from '../types'

const navigation = [{ id: 'courses', label: 'My courses', icon: BookOpen }, { id: 'library', label: 'Source library', icon: Folder }, { id: 'settings', label: 'Settings', icon: Settings }] as const
export function Shell({ view, onView, children, breadcrumb }: { view: View; onView: (view: View) => void; children: ReactNode; breadcrumb: string }) {
  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <button className="brand" onClick={() => onView('courses')} aria-label="Easy Street home"><svg width="45" height="33" viewBox="0 0 45 33" fill="none" aria-hidden="true"><path d="M1 4C9 1 16 2 23 7C30 1 37 1 44 4V30C37 27 29 28 23 32C17 28 8 27 1 30Z" fill="currentColor"/><path d="M28 3C14 10 17 12 28 16C38 20 25 25 15 30" stroke="#fffdf7" strokeWidth="4"/></svg><span>Easy Street</span></button>
      <nav aria-label="Main navigation">{navigation.map(({ id, label }) => <button key={id} className={`nav-link ${view === id ? 'active' : ''}`} onClick={() => onView(id)} aria-current={view === id ? 'page' : undefined}>{label}</button>)}</nav>
    </header>
    <main id="main" className="main-shell" aria-label={breadcrumb}>{children}</main>
    <footer className="site-footer"><span><LockKeyhole size={16}/>Your files stay on your device. Only selected excerpts go to OpenAI when you choose to generate.</span><span>Free software. Your API key.</span><span className="workspace"><span className="status-dot"/>Local workspace</span></footer>
  </div>
}
