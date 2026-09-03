import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface SHAPProps {
  contributions: Record<string, number>
  topFactors?: string[]
}

const FEATURE_LABELS: Record<string, string> = {
  flood_history: 'Flood History',
  landslide_history: 'Landslide History',
  seismic_zone: 'Seismic Zone',
  rainfall_mm: 'Rainfall',
  river_dist_km: 'River Proximity',
  slope: 'Slope',
  poverty_index: 'Poverty',
  age_vulnerability: 'Age Vulnerability',
  disability_index: 'Disability',
  infra_quality: 'Infrastructure',
  population: 'Population',
  area_sq_km: 'Area',
  elevation: 'Elevation',
  road_dist_km: 'Road Access',
  pop_density: 'Pop Density',
}

export default function SHAPWaterfall({ contributions, topFactors = [] }: SHAPProps) {
  const data = Object.entries(contributions)
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
      <h3 className="text-sm font-semibold mb-2">Feature Contributions (SHAP)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ left: 100 }}>
          <XAxis type="number" fontSize={11} />
          <YAxis type="category" dataKey="feature" fontSize={11} width={100} />
          <Tooltip
            formatter={(val: number) => [`${(val * 100).toFixed(2)}%`, 'Contribution']}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((d) => (
              <Cell
                key={d.rawKey}
                fill={d.value > 0 ? (d.isTop ? '#dc2626' : '#fca5a5') : (d.isTop ? '#16a34a' : '#86efac')}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 text-xs text-gray-500 mt-2">
        <span><span className="inline-block w-3 h-3 bg-red-600 rounded mr-1" /> Increases risk</span>
        <span><span className="inline-block w-3 h-3 bg-green-600 rounded mr-1" /> Decreases risk</span>
      </div>
    </div>
  )
}
