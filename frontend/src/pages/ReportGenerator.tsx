import { useState } from 'react'

export default function ReportGenerator() {
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [reportType, setReportType] = useState('sitrep')

  const generate = async () => {
    setLoading(true)
    if (reportType === 'sitrep') {
      const res = await fetch('/api/drie/report/sitrep')
      const data = await res.json()
      setReport(data)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Report Generator</h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>AI-generated situation reports and analyses</p>
        </div>
      </div>

      <div className="glass-card p-5 space-y-3">
        <div className="grid md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Report Type</label>
            <select value={reportType} onChange={e => setReportType(e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}>
              <option value="sitrep">Situation Report (SitRep)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={generate}
              disabled={loading}
              className="text-white px-6 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 transition-all shadow-lg"
              style={{ background: 'linear-gradient(135deg, #106EAB, #0D5A8C)' }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating...
                </span>
              ) : 'Generate Report'}
            </button>
          </div>
        </div>
      </div>

      {report && (
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold" style={{ color: 'var(--color-text)' }}>{report.report_type}</h2>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
              report.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
              report.severity === 'high' ? 'bg-accent/20 text-accent' :
              'bg-amber-500/20 text-amber-400'
            }`}>
              {report.severity?.toUpperCase()}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><span style={{ color: 'var(--color-text-muted)' }}>Habitations:</span> <span style={{ color: 'var(--color-text)' }}>{report.metadata?.total_habitations}</span></div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Population:</span> <span style={{ color: 'var(--color-text)' }}>{report.metadata?.total_population?.toLocaleString()}</span></div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Immediate:</span> <span style={{ color: 'var(--color-text)' }}>{report.metadata?.immediate_count}</span></div>
          </div>
          <pre className="rounded-xl p-4 text-sm whitespace-pre-wrap font-mono max-h-[500px] overflow-y-auto" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
            {report.text}
          </pre>
        </div>
      )}
    </div>
  )
}
