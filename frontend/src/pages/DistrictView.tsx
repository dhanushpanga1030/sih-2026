import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import RiskBadge from '../components/RiskBadge'

const BAND_COLORS = { immediate: '#ef4444', short_term: '#EF8C0A', medium_term: '#eab308', monitor: '#22c55e' }

export default function DistrictView() {
  const { name } = useParams()
  const [district, setDistrict] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/districts/${encodeURIComponent(name!)}`)
      .then(r => r.json())
      .then(d => { setDistrict(d); setLoading(false) })
  }, [name])

  if (loading || !district) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading district...</span>
      </div>
    </div>
  )

  const bandData = Object.entries(
    district.habitations.reduce((acc: Record<string, number>, h: any) => {
      acc[h.risk.band] = (acc[h.risk.band] || 0) + 1
      return acc
    }, {})
  ).map(([key, val]) => ({ name: key.replace('_', ' '), count: val, band: key }))

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
        <Link to="/" className="hover:underline" style={{ color: 'var(--color-primary)' }}>Assam</Link>
        <span>/</span>
        <span className="font-medium" style={{ color: 'var(--color-text)' }}>{district.name}</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #106EAB, #79C5DC)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{district.name} District</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{district.habitations.length} habitations · {district.total_population?.toLocaleString()} population</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Habitations</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{district.habitations.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Population</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{district.total_population?.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>High Risk</div>
            <div className="text-xl font-bold text-accent">{district.high_risk_count}</div>
          </CardContent>
        </Card>
      </div>

      {district.census_2011 && Object.keys(district.census_2011).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Census 2011</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Total Population</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.total_population?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Households</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.total_households?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Sex Ratio</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.sex_ratio}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Literacy Rate</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.literacy_rate}%</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>SC Population</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.total_sc?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>ST Population</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.total_st?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Health Facilities</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.health?.total_facilities}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Schools</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{district.census_2011.education?.total_schools}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Risk Distribution</CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Habitations (ranked by risk)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left" style={{ borderColor: 'var(--color-border)' }}>
                  {['Habitation', 'Population', 'Hazard', 'Vulnerability', 'Risk', 'Band'].map(h => (
                    <th key={h} className="pb-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {district.habitations.map((h: any) => (
                  <tr key={h.name} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--color-border)' }}>
                    <td className="py-2.5">
                      <Link to={`/habitation/${encodeURIComponent(h.name)}`} className="font-medium hover:underline" style={{ color: 'var(--color-primary)' }}>
                        {h.name}
                      </Link>
                    </td>
                    <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{h.population.toLocaleString()}</td>
                    <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{(h.hazard.combined * 100).toFixed(0)}%</td>
                    <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{(h.vulnerability.combined * 100).toFixed(0)}%</td>
                    <td className="py-2.5 font-mono" style={{ color: 'var(--color-text)' }}>{(h.risk.overall * 100).toFixed(0)}%</td>
                    <td className="py-2.5"><RiskBadge band={h.risk.band} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
