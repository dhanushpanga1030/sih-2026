import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import { useTheme } from '../theme'

interface Point {
  name: string
  lat: number
  lon: number
  [key: string]: any
}

interface MapViewProps {
  points: Point[]
  colorField?: string
  onClick?: (point: Point) => void
  height?: string
}

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
const LIGHT_STYLE = 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json'

export default function MapView({ points, colorField = 'band', onClick, height = '400px' }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!container.current || map.current) return

    map.current = new maplibregl.Map({
      container: container.current,
      style: theme === 'dark' ? DARK_STYLE : LIGHT_STYLE,
      center: [92.5, 26.5],
      zoom: 6,
      attributionControl: true,
    })

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.current.on('load', () => {
      const source: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: points.map((p) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
          properties: { ...p },
        })),
      }

      map.current!.addSource('points', { type: 'geojson', data: source })

      map.current!.addLayer({
        id: 'points-glow',
        type: 'circle',
        source: 'points',
        paint: {
          'circle-radius': 14,
          'circle-color': [
            'match', ['get', colorField],
            'immediate', 'rgba(239, 68, 68, 0.35)',
            'short_term', 'rgba(239, 140, 10, 0.35)',
            'medium_term', 'rgba(234, 179, 8, 0.3)',
            'monitor', 'rgba(34, 197, 94, 0.3)',
            'rgba(121, 197, 220, 0.2)',
          ],
          'circle-blur': 1,
        },
      })

      map.current!.addLayer({
        id: 'points-circle',
        type: 'circle',
        source: 'points',
        paint: {
          'circle-radius': 7,
          'circle-color': [
            'match', ['get', colorField],
            'immediate', '#ef4444',
            'short_term', '#EF8C0A',
            'medium_term', '#eab308',
            'monitor', '#22c55e',
            '#79C5DC',
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': theme === 'dark' ? '#0A2540' : '#ffffff',
        },
      })

      map.current!.on('click', 'points-circle', (e) => {
        if (e.features && e.features[0] && onClick) {
          onClick(e.features[0].properties as Point)
        }
      })

      map.current!.on('mouseenter', 'points-circle', () => {
        map.current!.getCanvas().style.cursor = 'pointer'
      })
      map.current!.on('mouseleave', 'points-circle', () => {
        map.current!.getCanvas().style.cursor = ''
      })

      if (points.length > 0) {
        const bounds = new maplibregl.LngLatBounds()
        points.forEach((p) => bounds.extend([p.lon, p.lat]))
        map.current!.fitBounds(bounds, { padding: 50 })
      }
    })

    return () => { map.current?.remove(); map.current = null }
  }, [theme])

  return (
    <div
      ref={container}
      className="rounded-xl overflow-hidden"
      style={{ height, width: '100%', border: '1px solid var(--color-border)' }}
    />
  )
}
