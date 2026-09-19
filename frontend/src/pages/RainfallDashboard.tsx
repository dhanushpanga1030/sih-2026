import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts'
import MapView from '../components/MapView'

interface DistrictRainfall {
  district: string
  total_mm: number
  station_count: number
  max_hourly_mm: number
  annual_rainfall_mm: Record<string, number>
  lat: number
  lon: number
}

interface TimeSeriesPoint {
  month: string
  rainfall_mm: number
}

export default function RainfallDashboard() {
  const [summary, setSummary] = useState<any>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<any>(null)
  const [timeseries, setTimeseries] = useState<TimeSeriesPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/rainfall/summary')
      .then(r => r.json())
      .then(d => { setSummary(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) { setDetail(null); setTimeseries([]); return }
    Promise.all([
      fetch(`/api/rainfall/district/${encodeURIComponent(selected)}`).then(r => r.json()),
      fetch(`/api/rainfall/timeseries/${encodeURIComponent(selected)}`).then(r => r.json()),
    ]).then(([d, ts]) => { setDetail(d); setTimeseries(ts.timeseries || []) })
  }, [selected])

  if (loading || !summary) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading rainfall data...</span>
      </div>
    </div>
  )

  const barData = summary.districts.map((d: DistrictRainfall) => ({
    name: d.district.length > 10 ? d.district.slice(0, 10) + '...' : d.district,
    fullName: d.district,
    total: d.total_mm,
    stations: d.station_count,
  }))

  const chartData = timeseries.map(ts => ({
    month: ts.month,
    rainfall: ts.rainfall_mm,
  }))

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #106EAB, #79C5DC)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Real Rainfall Data</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>IMD telemetry &amp; manual observations — {summary.total_districts} districts, {summary.total_records.toLocaleString()} records</p>
        </div>
      </div>

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Total Rainfall by District (mm)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData} onClick={(e) => e?.activePayload?.[0]?.payload?.fullName && setSelected(e.activePayload[0].payload.fullName)}>
            <XAxis dataKey="name" fontSize={10} angle={-35} textAnchor="end" height={70} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
            <YAxis fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
            <Tooltip
              contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text)' }}
              formatter={(val: number, name: string) => name === 'total' ? [`${val.toLocaleString()} mm`, 'Total Rainfall'] : [val, 'Stations']}
            />
            <Bar dataKey="total" fill="#106EAB" radius={[4, 4, 0, 0]} name="total" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>Click a bar to see district details</p>
      </div>

      {selected && detail && (
        <>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold" style={{ color: 'var(--color-text)' }}>{selected}</h2>
            <button onClick={() => setSelected(null)} className="text-xs px-3 py-1 rounded-full" style={{ background: 'var(--color-surface)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' }}>
              Clear selection
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Total Rainfall</div>
              <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{detail.total_mm?.toLocaleString()} mm</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Stations</div>
              <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{detail.station_count}</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Max Hourly</div>
              <div className="text-xl font-bold text-accent">{detail.max_hourly_mm} mm</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Records</div>
              <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{detail.n_records?.toLocaleString()}</div>
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="glass-card p-5">
              <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Monthly Rainfall — {selected}</h2>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="month" fontSize={10} angle={-35} textAnchor="end" height={60} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
                  <YAxis fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
                  <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text)' }} />
                  <Line type="monotone" dataKey="rainfall" stroke="#106EAB" strokeWidth={2} dot={false} name="Rainfall (mm)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {detail.annual_rainfall_mm && (
            <div className="glass-card p-5">
              <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Annual Totals</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(detail.annual_rainfall_mm).map(([year, mm]) => (
                  <div key={year} className="rounded-xl p-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                    <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{year}</div>
                    <div className="text-lg font-bold" style={{ color: 'var(--color-text)' }}>{(mm as number).toLocaleString()} mm</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {detail.stations && (
            <div className="glass-card p-5">
              <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Monitoring Stations</h2>
              <div className="flex flex-wrap gap-2">
                {detail.stations.map((st: string) => (
                  <span key={st} className="text-xs px-3 py-1 rounded-full" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
                    {st}
                  </span>
                ))}
              </div>
            </div>
          )}

          {detail.river_water_level && (
            <div className="glass-card p-5 border-l-4 border-l-navy-400">
              <h2 className="font-semibold mb-3" style={{ color: 'var(--color-text)' }}>River Water Level</h2>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div><span style={{ color: 'var(--color-text-muted)' }}>Stations:</span> <span style={{ color: 'var(--color-text)' }}>{detail.river_water_level.station_count}</span></div>
                <div><span style={{ color: 'var(--color-text-muted)' }}>Max Level:</span> <span style={{ color: 'var(--color-text)' }}>{detail.river_water_level.max_level_m} m</span></div>
                <div><span style={{ color: 'var(--color-text-muted)' }}>Min Level:</span> <span style={{ color: 'var(--color-text)' }}>{detail.river_water_level.min_level_m} m</span></div>
              </div>
            </div>
          )}
        </>
      )}

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Station Locations</h2>
        <MapView
          points={summary.districts.filter((d: DistrictRainfall) => d.lat && d.lon).map((d: DistrictRainfall) => ({
            name: d.district,
            lat: d.lat,
            lon: d.lon,
            band: d.total_mm > 5000 ? 'immediate' : d.total_mm > 2000 ? 'short_term' : 'monitor',
          }))}
          height="400px"
          onClick={(p) => setSelected(p.name)}
        />
      </div>
    </div>
  )
}
