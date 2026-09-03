const BAND_COLORS: Record<string, string> = {
  immediate: 'bg-red-600',
  short_term: 'bg-orange-500',
  medium_term: 'bg-yellow-500',
  monitor: 'bg-green-600',
}

const BAND_LABELS: Record<string, string> = {
  immediate: 'Immediate',
  short_term: 'Short-term',
  medium_term: 'Medium-term',
  monitor: 'Monitor',
}

export default function RiskBadge({ band }: { band: string }) {
  return (
    <span className={`risk-badge ${BAND_COLORS[band] || 'bg-gray-400'}`}>
      {BAND_LABELS[band] || band}
    </span>
  )
}
