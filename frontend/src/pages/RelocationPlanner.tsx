import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import RiskBadge from '../components/RiskBadge'

export default function RelocationPlanner() {
  const { name } = useParams<{ name: string }>()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!name) return
    Promise.all([
      fetch(`/api/drie/analyze/${encodeURIComponent(name)}`).then(r => r.json()),
      fetch(`/api/drie/match/${encodeURIComponent(name)}`).then(r => r.json()),
    ]).then(([analysis, matching]) => {
      setData({ analysis, matching })
      setLoading(false)
    }).catch(() => { setError('Failed to load relocation data'); setLoading(false) })
  }, [name])

  if (loading) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading relocation plan...</span>
      </div>
    </div>
  )
  if (error) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4 border-l-4 border-l-red-500">
        <span className="text-sm text-red-400">{error}</span>
      </div>
    </div>
  )
  if (!data) return null

  const { analysis, matching } = data
  const household = analysis.household_breakdown
  const priorities = household?.evacuation_priorities || {}

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #EF8C0A, #C97508)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Relocation Plan — {name}</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Evacuation priorities, site allocation, and route intelligence</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-3">
        <div className="glass-card p-4">
          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Population</div>
          <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{analysis.population?.toLocaleString()}</div>
        </div>
        <div className="glass-card p-4">
          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Risk Score</div>
          <div className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
            {((analysis.risk_assessment?.risk_score || 0) * 100).toFixed(0)}%
            <RiskBadge band={analysis.risk_assessment?.risk_band} />
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Site Coverage</div>
          <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{matching.coverage_pct}%</div>
          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{matching.sites_used} sites used</div>
        </div>
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Evacuation Priorities</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(priorities).map(([key, val]: [string, any]) => (
            <div key={key} className="rounded-xl p-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
              <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>{key.replace(/_/g, ' ')}</div>
              <div className="text-lg font-bold mt-1" style={{ color: 'var(--color-text)' }}>{val.count?.toLocaleString()}</div>
              <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>{val.description}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Site Allocations</h2>
        {matching.allocations?.length === 0 ? (
          <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No matching sites found.</p>
        ) : (
          <div className="space-y-3">
            {matching.allocations?.map((a: any, i: number) => (
              <div key={i} className="flex items-center justify-between rounded-xl p-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div>
                  <div className="font-medium" style={{ color: 'var(--color-text)' }}>{a.site_name}</div>
                  <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{a.route_type} route</div>
                </div>
                <div className="text-right">
                  <div className="font-mono" style={{ color: 'var(--color-text)' }}>{a.allocated_population.toLocaleString()} people</div>
                  <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{a.capacity_utilization}% capacity</div>
                </div>
              </div>
            ))}
          </div>
        )}
        {matching.unallocated > 0 && (
          <div className="mt-3 bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400">
            {matching.unallocated.toLocaleString()} residents require additional sites.
          </div>
        )}
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Route Intelligence</h2>
        {analysis.route_intelligence?.primary_route ? (
          <div className="grid md:grid-cols-2 gap-4">
            <div className="rounded-xl p-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
              <div className="text-sm font-medium text-emerald-400">Primary Route</div>
              <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{analysis.route_intelligence.primary_route.distance_km} km — {analysis.route_intelligence.primary_route.duration_hours}h</div>
              <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>Safety: {(analysis.route_intelligence.primary_route.safety_analysis?.safety_score * 100).toFixed(0)}%</div>
            </div>
            {analysis.route_intelligence.backup_route && (
              <div className="rounded-xl p-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div className="text-sm font-medium" style={{ color: 'var(--color-primary)' }}>Backup Route</div>
                <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{analysis.route_intelligence.backup_route.distance_km} km — {analysis.route_intelligence.backup_route.duration_hours}h</div>
                <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>Safety: {(analysis.route_intelligence.backup_route.safety_analysis?.safety_score * 100).toFixed(0)}%</div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>Route data unavailable (OSRM offline).</p>
        )}
      </div>

      <div className="glass-card p-4 border-l-4 border-l-navy-400">
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>AI-generated recommendation. Final decisions rest with DDMA/SDMA officials.</p>
      </div>
    </div>
  )
}
