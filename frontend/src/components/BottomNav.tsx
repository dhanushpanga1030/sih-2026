import { Link, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
  { to: '/overview', label: 'Districts', icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
  { to: '/scenario', label: 'Simulate', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { to: '/workflow', label: 'Workflow', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
  { to: '/rainfall', label: 'Rainfall', icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z' },
]

export default function BottomNav() {
  const location = useLocation()

  return (
    <nav className="pointer-events-auto absolute inset-x-0 bottom-4 z-30 mx-auto max-w-lg px-3">
      <div className="flex overflow-hidden rounded-2xl glass shadow-2xl">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(item.to))
          return (
            <Link
              key={item.to}
              to={item.to}
              className="flex flex-1 flex-col items-center gap-0.5 py-2.5 transition-all"
              style={{
                color: isActive ? '#106EAB' : 'var(--color-text-muted)',
                background: isActive ? 'rgba(16,110,171,0.1)' : 'transparent',
              }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              <span className="text-[10px] font-semibold leading-none">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
