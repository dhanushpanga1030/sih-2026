import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import RiskBadge from '../components/RiskBadge'

interface DREResult {
  habitation: string
  population: number
  risk_assessment: { risk_score: number; risk_band: string }
  confidence: { score: number; label: string }
  site_matching: { coverage_pct: number; unallocated: number }
}

export default function ExecutiveDashboard() {
  const [results, setResults] = useState<DREResult[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/drie/analyze-all')
      .then(r => r.json())
      .then(d => { setResults(d.results || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Running DRIE analysis...</span>
      </div>
    </div>
  )

  const immediate = results.filter(r => r.risk_assessment.risk_band === 'immediate')
  const shortTerm = results.filter(r => r.risk_assessment.risk_band === 'short_term')
  const totalPop = results.reduce((s, r) => s + r.population, 0)
  const atRiskPop = immediate.reduce((s, r) => s + r.population, 0) + shortTerm.reduce((s, r) => s + r.population, 0)

  return (
    <div className="space-y-5">
      <div className="glass-card p-4 border-l-4 border-l-accent">
        <div className="flex items-center gap-2 mb-1">
          <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-semibold text-accent">Dynamic Relocation Intelligence Engine</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>AI-powered multi-hazard risk assessment with SHAP explainability and relocation planning.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Total Habitations" value={results.length} />
        <StatCard label="Total Population" value={totalPop.toLocaleString()} />
        <StatCard label="Immediate" value={immediate.length} accent />
        <StatCard label="At-Risk Population" value={atRiskPop.toLocaleString()} accent />
        <StatCard label="Avg Confidence" value={`${(results.reduce((s, r) => s + r.confidence.score, 0) / Math.max(results.length, 1) * 100).toFixed(0)}%`} />
      </div>

      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-live" />
          <h2 className="font-semibold" style={{ color: 'var(--color-text)' }}>Immediate Priority — Relocation Required</h2>
        </div>
        {immediate.length === 0 ? (
          <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No habitations currently classified as immediate priority.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left" style={{ borderColor: 'var(--color-border)' }}>
                  {['Habitation', 'Population', 'Risk', 'Band', 'Coverage', 'Confidence', ''].map(h => (
                    <th key={h} className="pb-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {immediate.map(r => (
                  <tr key={r.habitation} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--color-border)' }}>
                    <td className="py-2.5 font-medium" style={{ color: 'var(--color-text)' }}>{r.habitation}</td>
                    <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{r.population.toLocaleString()}</td>
                    <td className="py-2.5 font-mono" style={{ color: 'var(--color-text)' }}>{(r.risk_assessment.risk_score * 100).toFixed(0)}%</td>
                    <td className="py-2.5"><RiskBadge band={r.risk_assessment.risk_band} /></td>
                    <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{r.site_matching.coverage_pct}%</td>
                    <td className="py-2.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${r.confidence.label === 'high' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400' : r.confidence.label === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-accent/20 dark:text-accent' : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'}`}>
                        {r.confidence.label}
                      </span>
                    </td>
                    <td className="py-2.5">
                      <Link to={`/habitation/${encodeURIComponent(r.habitation)}`} className="text-navy-500 dark:text-navy-300 hover:underline text-xs font-medium">View →</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>All Habitations by Risk</h2>
        <div className="max-h-[400px] overflow-y-auto space-y-1">
          {results.sort((a, b) => b.risk_assessment.risk_score - a.risk_assessment.risk_score).map(r => (
            <Link
              key={r.habitation}
              to={`/habitation/${encodeURIComponent(r.habitation)}`}
              className="flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all hover:opacity-80"
            >
              <span style={{ color: 'var(--color-text)' }}>{r.habitation}</span>
              <div className="flex items-center gap-3">
                <span className="font-mono" style={{ color: 'var(--color-text-secondary)' }}>{(r.risk_assessment.risk_score * 100).toFixed(0)}%</span>
                <RiskBadge band={r.risk_assessment.risk_band} />
              </div>
            </Link>
          ))}
        </div>
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
