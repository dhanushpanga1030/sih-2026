import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useTheme } from '../theme'

export default function Header() {
  const { theme, toggle } = useTheme()
  const [apiStatus, setApiStatus] = useState<'live' | 'connecting' | 'error'>('connecting')

  useEffect(() => {
    fetch('/api/state/summary')
      .then(() => setApiStatus('live'))
      .catch(() => setApiStatus('error'))
  }, [])

  const statusColors = {
    live: 'bg-emerald-400',
    connecting: 'bg-accent animate-live',
    error: 'bg-red-400',
  }

  return (
    <header className="pointer-events-none absolute left-0 top-0 z-20 flex max-w-[min(28rem,calc(100%-5rem))] flex-col gap-2 p-3">
      <div className="pointer-events-auto flex flex-wrap items-center gap-2">
        <Link to="/" className="glass-pill px-3 py-2 shadow-lg flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #106EAB, #79C5DC)' }}>
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-bold leading-tight" style={{ color: 'var(--color-text)' }}>SafeHabitat AI</h1>
            <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>AI-Powered Risk Platform — Assam</p>
          </div>
        </Link>

        <div className="glass-pill px-2.5 py-1 flex items-center gap-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${statusColors[apiStatus]}`} />
          <span className="text-[10px] font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
            {apiStatus === 'live' ? 'LIVE' : apiStatus === 'connecting' ? 'CONNECTING' : 'OFFLINE'}
          </span>
        </div>

        <button
          onClick={toggle}
          className="glass-pill px-2.5 py-1.5 flex items-center gap-1.5 transition-colors hover:opacity-80"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" style={{ color: 'var(--color-primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
      </div>

      <div className="pointer-events-auto">
        <div className="glass-pill px-3 py-1.5 inline-flex items-center gap-3 text-[11px]">
          <span style={{ color: 'var(--color-text-muted)' }}>DRIE Engine</span>
          <span style={{ color: 'var(--color-border)' }}>|</span>
          <span style={{ color: 'var(--color-text-secondary)' }}>35 Districts</span>
          <span style={{ color: 'var(--color-border)' }}>|</span>
          <span style={{ color: 'var(--color-text-secondary)' }}>158 Habitations</span>
        </div>
      </div>
    </header>
  )
}
