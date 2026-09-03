import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import MapView from '../components/MapView'
import RiskBadge from '../components/RiskBadge'
import { useNavigate } from 'react-router-dom'

interface Summary {
  state: string
  total_districts: number
  total_habitations: number
  total_population: number
  high_risk_count: number
  people_at_risk: number
  band_distribution: Record<string, number>
}

const BAND_COLORS = { immediate: '#dc2626', short_term: '#ea580c', medium_term: '#ca8a04', monitor: '#16a34a' }

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

  if (loading || !summary) return <div className="py-20 text-center text-gray-500">Loading Assam data...</div>

  const bandData = Object.entries(summary.band_distribution).map(([key, val]) => ({
    name: key.replace('_', ' '), count: val, band: key,
  }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Assam — State Overview</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Districts" value={summary.total_districts} />
        <StatCard label="Habitations" value={summary.total_habitations} />
        <StatCard label="Population" value={summary.total_population.toLocaleString()} />
        <StatCard label="People at Risk" value={summary.people_at_risk.toLocaleString()} color="text-red-600" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Risk Band Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={bandData}>
              <XAxis dataKey="name" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {bandData.map((d) => (
                  <Cell key={d.band} fill={BAND_COLORS[d.band as keyof typeof BAND_COLORS]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Top 10 High-Risk Habitations</h2>
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {habitations.slice(0, 10).map((h) => (
              <Link
                key={h.name}
                to={`/habitation/${encodeURIComponent(h.name)}`}
                className="flex items-center justify-between hover:bg-gray-50 px-2 py-1 rounded"
              >
                <div>
                  <span className="font-medium text-sm">{h.name}</span>
                  <span className="text-xs text-gray-500 ml-2">{h.district}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono">{(h.risk_score * 100).toFixed(0)}%</span>
                  <RiskBadge band={h.band} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h2 className="font-semibold mb-3">Habitat Risk Map</h2>
        <MapView
          points={habitations}
          height="500px"
          onClick={(p) => navigate(`/habitation/${encodeURIComponent(p.name)}`)}
        />
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`text-2xl font-bold ${color || ''}`}>{value}</div>
    </div>
  )
}
