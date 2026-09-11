import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import StateOverview from './pages/StateOverview'
import DistrictView from './pages/DistrictView'
import HabitationDetail from './pages/HabitationDetail'
import ScenarioSim from './pages/ScenarioSim'
import EvacuationRoute from './pages/EvacuationRoute'
import Reports from './pages/Reports'

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<StateOverview />} />
          <Route path="/district/:name" element={<DistrictView />} />
          <Route path="/habitation/:name" element={<HabitationDetail />} />
          <Route path="/scenario" element={<ScenarioSim />} />
          <Route path="/evacuation/:name" element={<EvacuationRoute />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
