import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'
import RiskBadge from '../components/RiskBadge'

const BAND_COLORS: Record<string, string> = {
  immediate: '#ef4444', short_term: '#EF8C0A', medium_term: '#eab308', monitor: '#22c55e',
}

interface Preset {
  name: string
  rainfall_delta: number
  seismic_magnitude: number
  landslide_trigger: number
  river_level_rise: number
  embankment_breach: boolean
}

export default function ScenarioSim() {
  const [rainfallDelta, setRainfallDelta] = useState(20)
  const [seismicMag, setSeismicMag] = useState(0)
  const [landslideTrigger, setLandslideTrigger] = useState(0)
  const [riverRise, setRiverRise] = useState(0)
  const [embankBreach, setEmbankBreach] = useState(false)
  const [target, setTarget] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [presets, setPresets] = useState<Preset[]>([])

  useEffect(() => {
    fetch('/api/drie/presets').then(r => r.json()).then(setPresets).catch(() => {})
  }, [])

  const applyPreset = (p: Preset) => {
    setRainfallDelta(p.rainfall_delta)
    setSeismicMag(p.seismic_magnitude)
    setLandslideTrigger(p.landslide_trigger)
    setRiverRise(p.river_level_rise)
    setEmbankBreach(p.embankment_breach)
  }

  const runScenario = async () => {
    setLoading(true)
    const res = await fetch('/api/drie/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rainfall_delta: rainfallDelta,
        habitation: target || undefined,
        seismic_magnitude: seismicMag,
        landslide_trigger: landslideTrigger,
        river_level_rise: riverRise,
        embankment_breach: embankBreach,
      }),
    })
    const data = await res.json()
    setResults(data.results || [])
    setLoading(false)
  }

  const changed = results.filter((r) => r.band_changed)
  const chartData = results.slice(0, 20).map((r) => ({
    name: r.habitation.length > 12 ? r.habitation.slice(0, 12) + '...' : r.habitation,
    original: r.original.risk * 100,
    simulated: r.simulated.risk * 100,
  }))

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #EF8C0A, #F5A623)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Scenario Simulation</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Multi-hazard what-if analysis with AI-driven risk recalculation</p>
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        {presets.length > 0 && (
          <div>
            <label className="block text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>Quick Presets</label>
            <div className="flex flex-wrap gap-2">
              {presets.map((p, i) => (
                <button key={i} onClick={() => applyPreset(p)} className="text-xs px-3 py-1.5 rounded-lg border transition-colors" style={{ background: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}>
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Rainfall Change (%)</label>
            <input type="range" min={-50} max={100} value={rainfallDelta} onChange={e => setRainfallDelta(Number(e.target.value))} className="w-full" />
            <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{rainfallDelta > 0 ? '+' : ''}{rainfallDelta}%</div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Seismic Magnitude (Richter)</label>
            <input type="range" min={0} max={8} step={0.5} value={seismicMag} onChange={e => setSeismicMag(Number(e.target.value))} className="w-full" />
            <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{seismicMag > 0 ? `${seismicMag} Richter` : 'None'}</div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Landslide Trigger (%)</label>
            <input type="range" min={0} max={100} value={landslideTrigger} onChange={e => setLandslideTrigger(Number(e.target.value))} className="w-full" />
            <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{landslideTrigger}%</div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>River Level Rise (%)</label>
            <input type="range" min={0} max={100} value={riverRise} onChange={e => setRiverRise(Number(e.target.value))} className="w-full" />
            <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{riverRise}%</div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={embankBreach} onChange={e => setEmbankBreach(e.target.checked)} id="embank" />
            <label htmlFor="embank" className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Embankment Breach</label>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Target Habitation (optional)</label>
            <input type="text" value={target} onChange={e => setTarget(e.target.value)} placeholder="Leave blank for all" className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} />
          </div>
        </div>
        <button onClick={runScenario} disabled={loading} className="text-white px-6 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 transition-all shadow-lg" style={{ background: 'linear-gradient(135deg, #106EAB, #0D5A8C)' }}>
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running...
            </span>
          ) : 'Run Multi-Hazard Simulation'}
        </button>
      </div>

      {results.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Habitations affected</div>
              <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{results.length}</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Band changes</div>
              <div className="text-xl font-bold text-accent">{changed.length}</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Newly "Immediate"</div>
              <div className="text-xl font-bold text-red-400">
                {changed.filter((r) => r.simulated.band === 'immediate' && r.original.band !== 'immediate').length}
              </div>
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="glass-card p-5">
              <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Risk Score Change (Top 20)</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" fontSize={10} angle={-30} textAnchor="end" height={60} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
                  <YAxis domain={[0, 100]} fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
                  <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text)' }} />
                  <Legend wrapperStyle={{ color: 'var(--color-text-muted)' }} />
                  <Bar dataKey="original" fill="#79C5DC" name="Original" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="simulated" fill="#EF8C0A" name="Simulated" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {changed.length > 0 && (
            <div className="glass-card p-5">
              <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Band Changes</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left" style={{ borderColor: 'var(--color-border)' }}>
                      {['Habitation', 'Original', 'Simulated', 'Change'].map(h => (
                        <th key={h} className="pb-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {changed.map((r) => (
                      <tr key={r.habitation} className="border-b transition-colors hover:opacity-80" style={{ borderColor: 'var(--color-border)' }}>
                        <td className="py-2.5" style={{ color: 'var(--color-text)' }}>{r.habitation}</td>
                        <td className="py-2.5">
                          <RiskBadge band={r.original.band} />
                          <span className="ml-2 font-mono" style={{ color: 'var(--color-text-secondary)' }}>{(r.original.risk * 100).toFixed(0)}%</span>
                        </td>
                        <td className="py-2.5">
                          <RiskBadge band={r.simulated.band} />
                          <span className="ml-2 font-mono" style={{ color: 'var(--color-text-secondary)' }}>{(r.simulated.risk * 100).toFixed(0)}%</span>
                        </td>
                        <td className="py-2.5 text-accent font-mono">
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
