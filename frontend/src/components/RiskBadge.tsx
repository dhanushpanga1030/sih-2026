import { Badge } from '@/components/ui/badge'

const BAND_VARIANTS: Record<string, 'destructive' | 'default' | 'secondary' | 'outline'> = {
  immediate: 'destructive',
  short_term: 'default',
  medium_term: 'secondary',
  monitor: 'outline',
}

const BAND_LABELS: Record<string, string> = {
  immediate: 'Immediate',
  short_term: 'Short-term',
  medium_term: 'Medium-term',
  monitor: 'Monitor',
}

export default function RiskBadge({ band }: { band: string }) {
  return (
    <Badge variant={BAND_VARIANTS[band] || 'secondary'}>
      {BAND_LABELS[band] || band}
    </Badge>
  )
}
