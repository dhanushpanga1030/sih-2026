import { useState, useEffect } from 'react'

const REPORT_TYPES = [
  { value: 'state', label: 'State Overview', desc: 'All districts summary' },
  { value: 'district', label: 'District Summary', desc: 'Habitations in a district' },
  { value: 'habitation', label: 'Habitation Risk', desc: 'Single habitation detail' },
  { value: 'relocation', label: 'Relocation Decision', desc: 'Ranked sites for a habitation' },
]

export default function Reports() {
  const [reportType, setReportType] = useState('state')
  const [districtName, setDistrictName] = useState('')
  const [habitationName, setHabitationName] = useState('')
  const [districts, setDistricts] = useState<string[]>([])
  const [downloading, setDownloading] = useState(false)

  // Complaint form
  const [complaint, setComplaint] = useState({
    reporter_name: '', phone: '', missing_person_name: '',
    last_seen_date: '', last_seen_location: '', description: '',
  })
  const [complaintMsg, setComplaintMsg] = useState('')

  useEffect(() => {
    fetch('/api/districts').then(r => r.json()).then(d =>
      setDistricts(d.map((x: any) => x.name).sort())
    )
  }, [])

  const downloadCSV = async () => {
    setDownloading(true)
    let url = '/api/reports/'
    if (reportType === 'state') url += 'state'
    else if (reportType === 'district') url += `district/${encodeURIComponent(districtName)}`
    else if (reportType === 'habitation') url += `habitation/${encodeURIComponent(habitationName)}`
    else if (reportType === 'relocation') url += `relocation/${encodeURIComponent(habitationName)}`

    const res = await fetch(url)
    if (res.ok) {
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'report.csv'
      a.click()
    }
    setDownloading(false)
  }

  const submitComplaint = async () => {
    setComplaintMsg('')
    const res = await fetch('/api/complaints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(complaint),
    })
    if (res.ok) {
      setComplaintMsg('Complaint filed successfully!')
      setComplaint({ reporter_name: '', phone: '', missing_person_name: '', last_seen_date: '', last_seen_location: '', description: '' })
    } else {
      setComplaintMsg('Failed to file complaint.')
    }
  }

  const needsDistrict = reportType === 'district'
  const needsHabitation = reportType === 'habitation' || reportType === 'relocation'
  const canDownload = reportType === 'state' || (needsDistrict && districtName) || (needsHabitation && habitationName)

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Reports & Complaints</h1>

      {/* Report Generator */}
      <div className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-lg font-semibold">Generate CSV Report</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              {REPORT_TYPES.map(r => (
                <option key={r.value} value={r.value}>{r.label} — {r.desc}</option>
              ))}
            </select>
          </div>
          {needsDistrict && (
            <div>
              <label className="block text-sm font-medium mb-1">District</label>
              <select
                value={districtName}
                onChange={(e) => setDistrictName(e.target.value)}
                className="w-full border rounded px-3 py-2"
              >
                <option value="">Select district</option>
                {districts.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          )}
          {needsHabitation && (
            <div>
              <label className="block text-sm font-medium mb-1">Habitation Name</label>
              <input
                type="text"
                value={habitationName}
                onChange={(e) => setHabitationName(e.target.value)}
                placeholder="e.g. Kamrup Village"
                className="w-full border rounded px-3 py-2"
              />
            </div>
          )}
        </div>
        <button
          onClick={downloadCSV}
          disabled={!canDownload || downloading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {downloading ? 'Downloading...' : 'Download CSV'}
        </button>
      </div>

      {/* Complaint Form */}
      <div className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-lg font-semibold">File Missing Person Complaint</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Your Name</label>
            <input
              type="text" value={complaint.reporter_name}
              onChange={(e) => setComplaint({ ...complaint, reporter_name: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
              type="tel" value={complaint.phone}
              onChange={(e) => setComplaint({ ...complaint, phone: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Missing Person Name</label>
            <input
              type="text" value={complaint.missing_person_name}
              onChange={(e) => setComplaint({ ...complaint, missing_person_name: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Last Seen Date</label>
            <input
              type="date" value={complaint.last_seen_date}
              onChange={(e) => setComplaint({ ...complaint, last_seen_date: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Last Seen Location</label>
            <input
              type="text" value={complaint.last_seen_location}
              onChange={(e) => setComplaint({ ...complaint, last_seen_location: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={complaint.description}
            onChange={(e) => setComplaint({ ...complaint, description: e.target.value })}
            rows={3}
            className="w-full border rounded px-3 py-2"
          />
        </div>
        <button
          onClick={submitComplaint}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          File Complaint
        </button>
        {complaintMsg && (
          <p className={`text-sm ${complaintMsg.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
            {complaintMsg}
          </p>
        )}
      </div>
    </div>
  )
}
