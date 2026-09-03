import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import RiskBadge from '../components/RiskBadge'

const BAND_COLORS = { immediate: '#dc2626', short_term: '#ea580c', medium_term: '#ca8a04', monitor: '#16a34a' }

export default function DistrictView() {
  const { name } = useParams()
  const [district, setDistrict] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/districts/${encodeURIComponent(name!)}`)
      .then(r => r.json())
      .then(d => { setDistrict(d); setLoading(false) })
  }, [name])

  if (loading || !district) return <div className="py-20 text-center text-gray-500">Loading district...</div>

  const bandData = Object.entries(
    district.habitations.reduce((acc: Record<string, number>, h: any) => {
      acc[h.risk.band] = (acc[h.risk.band] || 0) + 1
      return acc
    }, {})
  ).map(([key, val]) => ({ name: key.replace('_', ' '), count: val, band: key }))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-blue-600">Assam</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{district.name}</span>
      </div>

      <h1 className="text-2xl font-bold">{district.name} District</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Habitations</div>
          <div className="text-2xl font-bold">{district.habitations.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Population</div>
          <div className="text-2xl font-bold">{district.total_population?.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">High Risk</div>
          <div className="text-2xl font-bold text-red-600">{district.high_risk_count}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h2 className="font-semibold mb-3">Risk Distribution</h2>
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
        <h2 className="font-semibold mb-3">Habitations (ranked by risk)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2">Habitation</th>
                <th className="pb-2">Population</th>
                <th className="pb-2">Hazard</th>
                <th className="pb-2">Vulnerability</th>
                <th className="pb-2">Risk</th>
                <th className="pb-2">Band</th>
              </tr>
            </thead>
            <tbody>
              {district.habitations.map((h: any) => (
                <tr key={h.name} className="border-b hover:bg-gray-50">
                  <td className="py-2">
                    <Link to={`/habitation/${encodeURIComponent(h.name)}`} className="text-blue-600 hover:underline">
                      {h.name}
                    </Link>
                  </td>
                  <td className="py-2">{h.population.toLocaleString()}</td>
                  <td className="py-2">{(h.hazard.combined * 100).toFixed(0)}%</td>
                  <td className="py-2">{(h.vulnerability.combined * 100).toFixed(0)}%</td>
                  <td className="py-2 font-mono">{(h.risk.overall * 100).toFixed(0)}%</td>
                  <td className="py-2"><RiskBadge band={h.risk.band} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
