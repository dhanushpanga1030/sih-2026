import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import RiskBadge from '../components/RiskBadge'

interface RouteData {
  site: string
  suitability_score: number
  carrying_capacity: any
  route: any
  safety: any
  logistics: any
}

interface EvacuationData {
  habitation: string
  risk_band: string
  risk_score: number
  population: number
  origin: { lat: number; lon: number }
  routes: RouteData[]
}

const BAND_COLORS: Record<string, string> = {
  immediate: '#dc2626', short_term: '#ea580c', medium_term: '#ca8a04', monitor: '#16a34a',
}

const ROUTE_COLORS = ['#2563eb', '#7c3aed', '#0891b2', '#059669', '#d97706', '#dc2626']

export default function EvacuationRoute() {
  const { name } = useParams()
  const [data, setData] = useState<EvacuationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedRoute, setSelectedRoute] = useState<number>(0)
  const [showDirections, setShowDirections] = useState(false)
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)

  useEffect(() => {
    fetch(`/api/evacuation/${encodeURIComponent(name!)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
  }, [name])

  useEffect(() => {
    if (!mapContainer.current || !data || map.current) return

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [data.origin.lon, data.origin.lat],
      zoom: 8,
    })

    m.on('load', () => {
      // Origin marker
      const originEl = document.createElement('div')
      originEl.className = 'evacuation-origin-marker'
      originEl.style.cssText = `
        width: 20px; height: 20px; border-radius: 50%;
        background: ${BAND_COLORS[data.risk_band] || '#dc2626'};
        border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        cursor: pointer;
      `
      new maplibregl.Marker({ element: originEl })
        .setLngLat([data.origin.lon, data.origin.lat])
        .setPopup(new maplibregl.Popup().setHTML(`<b>${data.habitation}</b><br/>Red Zone Origin`))
        .addTo(m)

      // Destination markers
      data.routes.forEach((r, i) => {
        const route = r.route
        if (!route || route.status !== 'success' || !route.geometry) return

        const coords = route.geometry.coordinates
        if (!coords || coords.length === 0) return

        // Route line
        m.addSource(`route-${i}`, {
          type: 'geojson',
          data: {
            type: 'Feature',
            geometry: route.geometry,
            properties: {},
          },
        })

        m.addLayer({
          id: `route-line-${i}`,
          type: 'line',
          source: `route-${i}`,
          paint: {
            'line-color': ROUTE_COLORS[i % ROUTE_COLORS.length],
            'line-width': i === selectedRoute ? 5 : 2,
            'line-opacity': i === selectedRoute ? 1 : 0.4,
          },
        })

        // Destination marker
        const lastCoord = coords[coords.length - 1]
        const destEl = document.createElement('div')
        destEl.style.cssText = `
          width: 16px; height: 16px; border-radius: 50%;
          background: #16a34a; border: 2px solid white;
          box-shadow: 0 1px 4px rgba(0,0,0,0.3); cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          font-size: 10px; color: white; font-weight: bold;
        `
        destEl.textContent = `${i + 1}`

        new maplibregl.Marker({ element: destEl })
          .setLngLat(lastCoord)
          .setPopup(new maplibregl.Popup().setHTML(
            `<b>${r.site}</b><br/>Suitability: ${(r.suitability_score * 100).toFixed(0)}%<br/>Distance: ${r.route.distance_km} km`
          ))
          .addTo(m)
      })

      // Fit bounds
      const bounds = new maplibregl.LngLatBounds()
      bounds.extend([data.origin.lon, data.origin.lat])
      data.routes.forEach(r => {
        const coords = r.route?.geometry?.coordinates
        if (coords) coords.forEach((c: number[]) => bounds.extend(c as [number, number]))
      })
      m.fitBounds(bounds, { padding: 60 })
    })

    map.current = m
    return () => { m.remove(); map.current = null }
  }, [data, selectedRoute])

  if (loading || !data) return <div className="py-20 text-center text-gray-500">Calculating evacuation routes...</div>

  const selected = data.routes[selectedRoute]
  const steps = selected?.route?.steps || []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-blue-600">Assam</Link>
        <span>/</span>
        <Link to={`/habitation/${encodeURIComponent(data.habitation)}`} className="hover:text-blue-600">{data.habitation}</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">Evacuation Routes</span>
      </div>

      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Evacuation Routes</h1>
        <RiskBadge band={data.risk_band} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Population to Evacuate</div>
          <div className="text-2xl font-bold">{data.population.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Safe Routes Found</div>
          <div className="text-2xl font-bold text-green-600">{data.routes.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Nearest Safe Zone</div>
          <div className="text-2xl font-bold">{data.routes[0]?.route?.distance_km || '—'} km</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Est. Evacuation Time</div>
          <div className="text-2xl font-bold">{data.routes[0]?.logistics?.estimated_hours || '—'} hrs</div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Route Map</h2>
          <div ref={mapContainer} style={{ height: '450px' }} className="rounded-lg" />
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3">Ranked Safe Zones</h2>
          <div className="space-y-2 max-h-[450px] overflow-y-auto">
            {data.routes.map((r, i) => (
              <button
                key={r.site}
                onClick={() => setSelectedRoute(i)}
                className={`w-full text-left p-3 rounded-lg border transition ${
                  i === selectedRoute ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{i + 1}. {r.site}</span>
                  <span className="text-xs font-mono">{(r.suitability_score * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{r.route?.distance_km || '—'} km</span>
                  <span>{r.route?.duration_hours || '—'} hrs</span>
                  <span className={r.carrying_capacity?.verdict === 'sufficient' ? 'text-green-600' : 'text-red-600'}>
                    {r.carrying_capacity?.verdict === 'sufficient' ? '✅ Capable' : '❌ Over'}
                  </span>
                </div>
                <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${r.suitability_score * 100}%`,
                      background: ROUTE_COLORS[i % ROUTE_COLORS.length],
                    }}
                  />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {selected && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border p-4">
            <h2 className="font-semibold mb-3">Route Details — {selected.site}</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-xs text-gray-500">Distance</div>
                <div className="text-lg font-bold">{selected.route?.distance_km || '—'} km</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Drive Time</div>
                <div className="text-lg font-bold">{selected.route?.duration_hours || '—'} hours</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Safety Score</div>
                <div className="text-lg font-bold">{selected.safety?.safety_score ? `${(selected.safety.safety_score * 100).toFixed(0)}%` : '—'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Flood Zones Crossed</div>
                <div className="text-lg font-bold">{selected.safety?.flood_zones_crossed ?? '—'}</div>
              </div>
            </div>

            <div className="border-t pt-3 mt-3">
              <h3 className="text-sm font-semibold mb-2">Logistics</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-500">Buses needed:</span> <b>{selected.logistics?.buses_needed}</b></div>
                <div><span className="text-gray-500">Trips:</span> <b>{selected.logistics?.trips_needed}</b></div>
                <div><span className="text-gray-500">Total distance:</span> <b>{selected.logistics?.total_distance_km} km</b></div>
                <div><span className="text-gray-500">Total time:</span> <b>{selected.logistics?.estimated_hours} hrs</b></div>
              </div>
            </div>

            <div className="border-t pt-3 mt-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold">Carrying Capacity</h3>
                <span className={`text-sm font-medium ${selected.carrying_capacity?.verdict === 'sufficient' ? 'text-green-600' : 'text-red-600'}`}>
                  {selected.carrying_capacity?.verdict === 'sufficient' ? '✅ Sufficient' : '❌ Insufficient'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-500">Incoming:</span> <b>{selected.carrying_capacity?.incoming_population?.toLocaleString()}</b></div>
                <div><span className="text-gray-500">Available:</span> <b>{selected.carrying_capacity?.available_capacity?.toLocaleString()}</b></div>
                <div><span className="text-gray-500">Gap:</span> <b className={selected.carrying_capacity?.capacity_gap >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {selected.carrying_capacity?.capacity_gap?.toLocaleString()}
                </b></div>
                <div><span className="text-gray-500">Infra rating:</span> <b>{(selected.carrying_capacity?.infrastructure_rating * 100)?.toFixed(0)}%</b></div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">Turn-by-Turn Directions</h2>
              <button
                onClick={() => setShowDirections(!showDirections)}
                className="text-xs text-blue-600 hover:underline"
              >
                {showDirections ? 'Hide' : 'Show'} ({steps.length} steps)
              </button>
            </div>

            {showDirections && steps.length > 0 ? (
              <div className="space-y-1 max-h-[400px] overflow-y-auto">
                {steps.map((step: any, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-sm py-1 border-b border-gray-50 last:border-0">
                    <span className="text-gray-400 text-xs mt-0.5 w-5 shrink-0">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{formatInstruction(step.instruction)}</span>
                        {step.name && <span className="text-gray-500">on {step.name}</span>}
                      </div>
                      <div className="text-xs text-gray-400">
                        {step.distance_km} km · {step.duration_min} min
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                {steps.length === 0 ? 'No turn-by-turn data available.' : 'Click "Show" to view directions.'}
              </p>
            )}
          </div>
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
        <b>Disclaimer:</b> This is an AI-generated evacuation route recommendation. Final evacuation decisions rest with authorized disaster management officials. Routes are calculated using OpenStreetMap road data and may not reflect real-time road conditions.
      </div>
    </div>
  )
}

function formatInstruction(type: string): string {
  const map: Record<string, string> = {
    depart: 'Depart',
    turn: 'Turn',
    'new name': 'Continue onto',
    merge: 'Merge',
    'on ramp': 'Enter ramp',
    'off ramp': 'Exit ramp',
    fork: 'Fork',
    'end of road': 'End of road',
    continue: 'Continue',
    roundabout: 'Enter roundabout',
    rotary: 'Enter rotary',
    'roundabout turn': 'Take roundabout exit',
    notification: 'Continue',
  }
  return map[type] || type.charAt(0).toUpperCase() + type.slice(1)
}
