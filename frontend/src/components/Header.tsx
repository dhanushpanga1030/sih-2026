import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl font-bold text-blue-700">SafeHabitat AI</span>
          <span className="text-sm text-gray-500">— Assam</span>
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/" className="hover:text-blue-600">State Overview</Link>
          <Link to="/scenario" className="hover:text-blue-600">Scenario Simulation</Link>
          <Link to="/reports" className="hover:text-blue-600">Reports</Link>
        </nav>
      </div>
    </header>
  )
}
