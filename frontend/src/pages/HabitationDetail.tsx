import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import RiskBadge from '../components/RiskBadge'
import MapView from '../components/MapView'
import SHAPWaterfall from '../components/SHAPWaterfall'

export default function HabitationDetail() {
  const { name } = useParams()
  const [hab, setHab] = useState<any>(null)
  const [explanation, setExplanation] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`/api/habitations/${encodeURIComponent(name!)}`).then(r => r.json()),
      fetch(`/api/habitations/${encodeURIComponent(name!)}/explain`).then(r => r.json()),
    ]).then(([h, e]) => { setHab(h); setExplanation(e); setLoading(false) })
  }, [name])

  if (loading || !hab) return <div className="py-20 text-center text-gray-500">Loading habitation...</div>

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
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-blue-600">Assam</Link>
        <span>/</span>
        <Link to={`/district/${encodeURIComponent(hab.district)}`} className="hover:text-blue-600">{hab.district}</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{hab.name}</span>
      </div>

      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">{hab.name}</h1>
        <RiskBadge band={hab.risk.band} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Population</div>
          <div className="text-2xl font-bold">{hab.population.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Risk Score</div>
          <div className="text-2xl font-bold">{(hab.risk.overall * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Confidence</div>
          <div className="text-2xl font-bold">{(hab.risk.confidence * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Area (sq km)</div>
          <div className="text-2xl font-bold">{hab.area_sq_km}</div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Hazard Breakdown</h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={hazardData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" fontSize={12} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} fontSize={10} />
              <Radar name="Hazard" dataKey="value" stroke="#dc2626" fill="#dc2626" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Vulnerability Breakdown</h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={vulnData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" fontSize={12} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} fontSize={10} />
              <Radar name="Vulnerability" dataKey="value" stroke="#ea580c" fill="#ea580c" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h2 className="font-semibold mb-2">Why this risk level?</h2>
        <div className="text-sm text-gray-700 whitespace-pre-line">{explanation.explanation}</div>
        <div className="mt-3 text-xs text-gray-400 italic">{explanation.disclaimer}</div>
        {explanation.model_info && (
          <div className="mt-2 text-xs text-gray-500">
            Model: {explanation.model_info.risk_model} | Explainability: {explanation.model_info.explainability}
          </div>
        )}
      </div>

      {explanation.shap_contributions && (
        <div className="bg-white rounded-lg border p-4">
          <SHAPWaterfall
            contributions={explanation.shap_contributions}
            topFactors={explanation.top_factors}
          />
        </div>
      )}

      <div className="bg-white rounded-lg border p-4">
        <h2 className="font-semibold mb-3">Relocation Site Candidates</h2>
        {hab.relocation_sites?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Site</th>
                  <th className="pb-2">Suitability</th>
                  <th className="pb-2">Capacity</th>
                  <th className="pb-2">Verdict</th>
                  <th className="pb-2">Safety</th>
                  <th className="pb-2">Road</th>
                  <th className="pb-2">Water</th>
                </tr>
              </thead>
              <tbody>
                {hab.relocation_sites.map((s: any) => (
                  <tr key={s.name} className="border-b hover:bg-gray-50">
                    <td className="py-2 font-medium">{s.name}</td>
                    <td className="py-2 font-mono">{(s.suitability_score * 100).toFixed(0)}%</td>
                    <td className="py-2">{s.max_capacity.toLocaleString()}</td>
                    <td className="py-2">
                      <span className={s.carrying_capacity.verdict === 'sufficient' ? 'text-green-600' : 'text-red-600'}>
                        {s.carrying_capacity.verdict === 'sufficient' ? '✅ Sufficient' : '❌ Insufficient'}
                      </span>
                    </td>
                    <td className="py-2">{(s.scores.safety * 100).toFixed(0)}%</td>
                    <td className="py-2">{(s.scores.road * 100).toFixed(0)}%</td>
                    <td className="py-2">{(s.scores.water * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No relocation sites evaluated.</p>
        )}
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h2 className="font-semibold mb-3">Map</h2>
        <MapView
          points={[
            { name: hab.name, lat: hab.lat, lon: hab.lon, band: hab.risk.band },
            ...(hab.relocation_sites || []).map((s: any) => ({
              name: s.name, lat: s.lat, lon: s.lon, band: 'monitor',
            })),
          ]}
          height="350px"
        />
      </div>
    </div>
  )
}
