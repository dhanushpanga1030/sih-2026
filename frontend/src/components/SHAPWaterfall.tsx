import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface SHAPProps {
  contributions: Record<string, number>
  topFactors?: string[]
}

const FEATURE_LABELS: Record<string, string> = {
  hazard_x_exposure: 'Hazard x Exposure',
  vuln_combined: 'Combined Vulnerability',
  infra_quality: 'Infrastructure',
  pop_density: 'Pop Density',
  poverty_index: 'Poverty',
  flood_score: 'Flood Risk',
  disability_index: 'Disability',
  exposure: 'Exposure',
  hazard_combined: 'Combined Hazard',
  flood_x_vuln: 'Flood x Vulnerability',
  seismic_score: 'Seismic',
  population: 'Population',
  area_sq_km: 'Area',
  hazard_index: 'Hazard Index',
  landslide_score: 'Landslide',
  avg_flood_duration: 'Flood Duration',
  flood_fatalities: 'Flood Fatalities',
  erosion_score: 'Erosion',
  age_vulnerability: 'Age Vulnerability',
  flooded_area_pct: 'Flooded Area',
  permanent_water: 'Permanent Water',
  flood_history: 'Flood History',
  landslide_history: 'Landslide History',
  seismic_zone: 'Seismic Zone',
  rainfall_mm: 'Rainfall',
  river_dist_km: 'River Proximity',
  slope: 'Slope',
  elevation: 'Elevation',
  road_dist_km: 'Road Access',
}

export default function SHAPWaterfall({ contributions, topFactors = [] }: SHAPProps) {
  const data = Object.entries(contributions)
    .filter(([_, val]) => Math.abs(val) > 0.0001)
    .map(([key, val]) => ({
      feature: FEATURE_LABELS[key] || key,
      value: val,
      rawKey: key,
      isTop: topFactors.includes(key),
    }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10)

  return (
    <div>
      <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text)' }}>Feature Contributions (SHAP)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ left: 120 }}>
          <XAxis type="number" fontSize={11} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-muted)' }} />
          <YAxis type="category" dataKey="feature" fontSize={11} width={120} stroke="var(--color-border)" tick={{ fill: 'var(--color-text-secondary)' }} />
          <Tooltip
            contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, color: 'var(--color-text)' }}
            formatter={(val: number) => [`${(val * 100).toFixed(2)}%`, 'Contribution']}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((d) => (
              <Cell
                key={d.rawKey}
                fill={d.value > 0 ? (d.isTop ? '#ef4444' : '#fca5a5') : (d.isTop ? '#22c55e' : '#86efac')}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
        <span><span className="inline-block w-3 h-3 bg-red-500 rounded mr-1" /> Increases risk</span>
        <span><span className="inline-block w-3 h-3 bg-emerald-500 rounded mr-1" /> Decreases risk</span>
      </div>
    </div>
  )
}
