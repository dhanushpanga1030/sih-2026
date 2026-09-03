import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'

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

export default function MapView({ points, colorField = 'band', onClick, height = '400px' }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)

  useEffect(() => {
    if (!container.current || map.current) return

    map.current = new maplibregl.Map({
      container: container.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [92.5, 26.5],
      zoom: 6,
    })

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
        id: 'points-circle',
        type: 'circle',
        source: 'points',
        paint: {
          'circle-radius': 7,
          'circle-color': [
            'match',
            ['get', colorField],
            'immediate', '#dc2626',
            'short_term', '#ea580c',
            'medium_term', '#ca8a04',
            'monitor', '#16a34a',
            '#999999',
          ],
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff',
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
  }, [])

  return <div ref={container} style={{ height, width: '100%' }} className="rounded-lg border" />
}
