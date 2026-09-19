import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import RiskBadge from '../components/RiskBadge'
import MapView from '../components/MapView'
import SHAPWaterfall from '../components/SHAPWaterfall'

export default function HabitationDetail() {
  const { name } = useParams()
  const navigate = useNavigate()
  const [hab, setHab] = useState<any>(null)
  const [explanation, setExplanation] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`/api/habitations/${encodeURIComponent(name!)}`).then(r => r.json()),
      fetch(`/api/habitations/${encodeURIComponent(name!)}/explain`).then(r => r.json()),
    ]).then(([h, e]) => { setHab(h); setExplanation(e); setLoading(false) })
  }, [name])

  if (loading || !hab) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading habitation...</span>
      </div>
    </div>
  )

  const hazardData = [
    { subject: 'Flood', value: hab.hazard.flood * 100 },
    { subject: 'Landslide', value: hab.hazard.landslide * 100 },
    { subject: 'Seismic', value: hab.hazard.seismic * 100 },
    { subject: 'Erosion', value: hab.hazard.erosion * 100 },
  ]

  const vulnData = [
    { subject: 'Poverty', value: hab.vulnerability.poverty_index * 100 },
    { subject: 'Age Vuln', value: hab.vulnerability.age_vulnerability * 100 },
    { subject: 'Disability', value: hab.vulnerability.disability_index * 100 },
    { subject: 'Infra Quality', value: (1 - hab.vulnerability.infrastructure_quality) * 100 },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
        <Link to="/" className="hover:underline" style={{ color: 'var(--color-primary)' }}>Assam</Link>
        <span>/</span>
        <Link to={`/district/${encodeURIComponent(hab.district)}`} className="hover:underline" style={{ color: 'var(--color-primary)' }}>{hab.district}</Link>
        <span>/</span>
        <span className="font-medium" style={{ color: 'var(--color-text)' }}>{hab.name}</span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{hab.name}</h1>
        <RiskBadge band={hab.risk.band} />
        {hab.risk.band === 'immediate' && (
          <button
            onClick={() => navigate(`/evacuation/${encodeURIComponent(hab.name)}`)}
            className="bg-red-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-red-700 flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            Find Safe Routes
          </button>
        )}
        <Link to={`/relocation/${encodeURIComponent(hab.name)}`} className="glass-pill px-4 py-1.5 text-sm font-medium transition-colors" style={{ color: 'var(--color-primary)' }}>
          Relocation Plan →
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Population</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{hab.population.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Risk Score</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{(hab.risk.overall * 100).toFixed(0)}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Confidence</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{(hab.risk.confidence * 100).toFixed(0)}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Area (sq km)</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{hab.area_sq_km}</div>
          </CardContent>
        </Card>
      </div>

      {hab.census_2011 && Object.keys(hab.census_2011).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Census 2011 — {hab.district}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Population</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.total_population?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Households</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.total_households?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Sex Ratio</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.sex_ratio}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Literacy Rate</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.literacy_rate}%</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Tap Water Access</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.water?.pct_tap_water?.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>All-Weather Road</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.transport?.pct_all_weather?.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Health Facilities</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.health?.total_facilities}</div>
              </div>
              <div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Forest Cover</div>
                <div className="font-bold" style={{ color: 'var(--color-text)' }}>{hab.census_2011.land_use?.pct_forest?.toFixed(1)}%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Hazard Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={hazardData}>
                <PolarGrid stroke="var(--color-border)" />
                <PolarAngleAxis dataKey="subject" fontSize={12} tick={{ fill: 'var(--color-text-secondary)' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} fontSize={10} tick={{ fill: 'var(--color-text-muted)' }} />
                <Radar name="Hazard" dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Vulnerability Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={vulnData}>
                <PolarGrid stroke="var(--color-border)" />
                <PolarAngleAxis dataKey="subject" fontSize={12} tick={{ fill: 'var(--color-text-secondary)' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} fontSize={10} tick={{ fill: 'var(--color-text-muted)' }} />
                <Radar name="Vulnerability" dataKey="value" stroke="#EF8C0A" fill="#EF8C0A" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Why this risk level?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm whitespace-pre-line leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>{explanation.explanation}</div>
          <div className="mt-3 text-xs italic" style={{ color: 'var(--color-text-muted)' }}>{explanation.disclaimer}</div>
          {explanation.model_info && (
            <div className="mt-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Model: {explanation.model_info.risk_model} | Explainability: {explanation.model_info.explainability}
            </div>
          )}
        </CardContent>
      </Card>

      {explanation.shap_contributions && (
        <Card>
          <CardContent className="p-5">
            <SHAPWaterfall
              contributions={explanation.shap_contributions}
              topFactors={explanation.top_factors}
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Relocation Site Candidates</CardTitle>
            {hab.risk.band === 'immediate' && (
              <button
                onClick={() => navigate(`/evacuation/${encodeURIComponent(hab.name)}`)}
                className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              >
                Find Safe Routes
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {hab.relocation_sites?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left" style={{ borderColor: 'var(--color-border)' }}>
                    {['Site', 'Suitability', 'Capacity', 'Verdict', 'Safety', 'Road', 'Water'].map(h => (
                      <th key={h} className="pb-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {hab.relocation_sites.map((s: any) => (
                    <tr key={s.name} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--color-border)' }}>
                      <td className="py-2.5 font-medium" style={{ color: 'var(--color-text)' }}>{s.name}</td>
                      <td className="py-2.5 font-mono" style={{ color: 'var(--color-text-secondary)' }}>{(s.suitability_score * 100).toFixed(0)}%</td>
                      <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{s.max_capacity.toLocaleString()}</td>
                      <td className="py-2.5">
                        <span className={s.carrying_capacity.verdict === 'sufficient' ? 'text-emerald-400' : 'text-red-400'}>
                          {s.carrying_capacity.verdict === 'sufficient' ? 'Sufficient' : 'Insufficient'}
                        </span>
                      </td>
                      <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{(s.scores.safety * 100).toFixed(0)}%</td>
                      <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{(s.scores.road * 100).toFixed(0)}%</td>
                      <td className="py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{(s.scores.water * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No relocation sites evaluated.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Map</CardTitle>
        </CardHeader>
        <CardContent>
          <MapView
            points={[
              { name: hab.name, lat: hab.lat, lon: hab.lon, band: hab.risk.band },
              ...(hab.relocation_sites || []).map((s: any) => ({
                name: s.name, lat: s.lat, lon: s.lon, band: 'monitor',
              })),
            ]}
            height="350px"
          />
        </CardContent>
      </Card>
    </div>
  )
}
