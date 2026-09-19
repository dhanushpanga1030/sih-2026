import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import MapView from '../components/MapView'
import RiskBadge from '../components/RiskBadge'

interface Summary {
  state: string
  total_districts: number
  total_habitations: number
  total_population: number
  high_risk_count: number
  people_at_risk: number
  band_distribution: Record<string, number>
}

const BAND_COLORS = { immediate: '#ef4444', short_term: '#EF8C0A', medium_term: '#eab308', monitor: '#22c55e' }

export default function StateOverview() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [habitations, setHabitations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      fetch('/api/state/summary').then(r => r.json()),
      fetch('/api/map/habitations').then(r => r.json()),
    ]).then(([s, h]) => { setSummary(s); setHabitations(h); setLoading(false) })
  }, [])

  if (loading || !summary) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading Assam data...</span>
      </div>
    </div>
  )

  const bandData = Object.entries(summary.band_distribution).map(([key, val]) => ({
    name: key.replace('_', ' '), count: val, band: key,
  }))

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #106EAB, #79C5DC)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Assam — State Overview</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>District-level risk monitoring and habitations</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Districts" value={summary.total_districts} />
        <StatCard label="Habitations" value={summary.total_habitations} />
        <StatCard label="Population" value={summary.total_population.toLocaleString()} />
        <StatCard label="People at Risk" value={summary.people_at_risk.toLocaleString()} accent />
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <div className="glass-card p-5">
          <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Risk Band Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={bandData}>
              <XAxis dataKey="name" fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} />
              <YAxis fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text)' }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {bandData.map((d) => (
                  <Cell key={d.band} fill={BAND_COLORS[d.band as keyof typeof BAND_COLORS]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-5">
          <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Top 10 High-Risk Habitations</h2>
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {habitations.slice(0, 10).map((h) => (
              <Link
                key={h.name}
                to={`/habitation/${encodeURIComponent(h.name)}`}
                className="flex items-center justify-between px-3 py-2 rounded-lg transition-all hover:opacity-80"
              >
                <div>
                  <span className="font-medium text-sm" style={{ color: 'var(--color-text)' }}>{h.name}</span>
                  <span className="text-xs ml-2" style={{ color: 'var(--color-text-muted)' }}>{h.district}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono" style={{ color: 'var(--color-text-secondary)' }}>{(h.risk_score * 100).toFixed(0)}%</span>
                  <RiskBadge band={h.band} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Habitation Risk Map</h2>
        <MapView
          points={habitations}
          height="500px"
          onClick={(p) => navigate(`/habitation/${encodeURIComponent(p.name)}`)}
        />
      </div>
    </div>
  )
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="glass-card p-4">
      <div className="text-xs mb-1" style={{ color: 'var(--color-text-muted)' }}>{label}</div>
      <div className="text-xl font-bold" style={{ color: accent ? 'var(--color-accent)' : 'var(--color-text)' }}>{value}</div>
    </div>
  )
}
