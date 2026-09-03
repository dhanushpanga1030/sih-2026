import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'
import RiskBadge from '../components/RiskBadge'

const BAND_COLORS: Record<string, string> = {
  immediate: '#dc2626', short_term: '#ea580c', medium_term: '#ca8a04', monitor: '#16a34a',
}

export default function ScenarioSim() {
  const [rainfallDelta, setRainfallDelta] = useState(20)
  const [target, setTarget] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const runScenario = async () => {
    setLoading(true)
    const res = await fetch('/api/scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rainfall_delta: rainfallDelta, habitation: target || undefined }),
    })
    const data = await res.json()
    setResults(data.results)
    setLoading(false)
  }

  const changed = results.filter((r) => r.band_changed)
  const chartData = results.slice(0, 20).map((r) => ({
    name: r.habitation.length > 12 ? r.habitation.slice(0, 12) + '...' : r.habitation,
    original: r.original.risk_score * 100,
    simulated: r.simulated.risk_score * 100,
  }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Scenario Simulation</h1>

      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Rainfall Change (%)</label>
            <input
              type="range"
              min={-50}
              max={100}
              value={rainfallDelta}
              onChange={(e) => setRainfallDelta(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-sm text-gray-600 mt-1">
              {rainfallDelta > 0 ? '+' : ''}{rainfallDelta}% rainfall
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Target Habitation (optional)</label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Leave blank for all"
              className="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          onClick={runScenario}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Running...' : 'Run Scenario'}
        </button>
      </div>

      {results.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-500">Habitations affected</div>
              <div className="text-2xl font-bold">{results.length}</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-500">Band changes</div>
              <div className="text-2xl font-bold text-orange-600">{changed.length}</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-500">Newly "Immediate"</div>
              <div className="text-2xl font-bold text-red-600">
                {changed.filter((r) => r.simulated.band === 'immediate' && r.original.band !== 'immediate').length}
              </div>
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="bg-white rounded-lg border p-4">
              <h2 className="font-semibold mb-3">Risk Score Change (Top 20)</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" fontSize={10} angle={-30} textAnchor="end" height={60} />
                  <YAxis domain={[0, 100]} fontSize={12} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="original" fill="#93c5fd" name="Original" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="simulated" fill="#f87171" name="Simulated" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {changed.length > 0 && (
            <div className="bg-white rounded-lg border p-4">
              <h2 className="font-semibold mb-3">Band Changes</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-gray-500">
                      <th className="pb-2">Habitation</th>
                      <th className="pb-2">Original</th>
                      <th className="pb-2">Simulated</th>
                      <th className="pb-2">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {changed.map((r) => (
                      <tr key={r.habitation} className="border-b hover:bg-gray-50">
                        <td className="py-2">{r.habitation}</td>
                        <td className="py-2">
                          <RiskBadge band={r.original.band} />
                          <span className="ml-2 font-mono">{(r.original.risk_score * 100).toFixed(0)}%</span>
                        </td>
                        <td className="py-2">
                          <RiskBadge band={r.simulated.band} />
                          <span className="ml-2 font-mono">{(r.simulated.risk_score * 100).toFixed(0)}%</span>
                        </td>
                        <td className="py-2 text-red-600 font-mono">
                          {r.risk_change > 0 ? '+' : ''}{(r.risk_change * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
