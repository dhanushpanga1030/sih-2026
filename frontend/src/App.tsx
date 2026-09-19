import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './theme'
import Header from './components/Header'
import BottomNav from './components/BottomNav'
import StateOverview from './pages/StateOverview'
import DistrictView from './pages/DistrictView'
import HabitationDetail from './pages/HabitationDetail'
import ScenarioSim from './pages/ScenarioSim'
import ExecutiveDashboard from './pages/ExecutiveDashboard'
import RelocationPlanner from './pages/RelocationPlanner'
import WorkflowPanel from './pages/WorkflowPanel'
import RainfallDashboard from './pages/RainfallDashboard'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="relative h-full w-full overflow-hidden" style={{ background: 'var(--color-bg)', color: 'var(--color-text)' }}>
          <Header />
          <main className="absolute inset-0 overflow-y-auto pt-28 pb-20">
            <div className="max-w-5xl mx-auto px-4 space-y-6">
              <Routes>
                <Route path="/" element={<ExecutiveDashboard />} />
                <Route path="/overview" element={<StateOverview />} />
                <Route path="/district/:name" element={<DistrictView />} />
                <Route path="/habitation/:name" element={<HabitationDetail />} />
                <Route path="/scenario" element={<ScenarioSim />} />
                <Route path="/relocation/:name" element={<RelocationPlanner />} />
                <Route path="/workflow" element={<WorkflowPanel />} />
                <Route path="/rainfall" element={<RainfallDashboard />} />
              </Routes>
            </div>
          </main>
          <BottomNav />
        </div>
      </BrowserRouter>
    </ThemeProvider>
  )
}
