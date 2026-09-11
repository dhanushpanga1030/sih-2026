import { useState } from 'react'

export default function Reports() {
  const [form, setForm] = useState({
    reporter_name: '', phone: '', missing_person_name: '',
    last_seen_date: '', last_seen_location: '', description: '',
  })
  const [photo, setPhoto] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [msg, setMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handlePhoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setPhoto(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  const submit = async () => {
    setMsg('')
    setSubmitting(true)
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => fd.append(k, v))
    if (photo) fd.append('photo', photo)

    const res = await fetch('/api/complaints', { method: 'POST', body: fd })
    if (res.ok) {
      setMsg('Complaint filed successfully!')
      setForm({ reporter_name: '', phone: '', missing_person_name: '', last_seen_date: '', last_seen_location: '', description: '' })
      setPhoto(null)
      setPreview('')
    } else {
      setMsg('Failed to file complaint.')
    }
    setSubmitting(false)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">File Missing Person Complaint</h1>

      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Your Name *</label>
            <input
              type="text" value={form.reporter_name}
              onChange={(e) => setForm({ ...form, reporter_name: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone *</label>
            <input
              type="tel" value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Missing Person Name *</label>
            <input
              type="text" value={form.missing_person_name}
              onChange={(e) => setForm({ ...form, missing_person_name: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Last Seen Date *</label>
            <input
              type="date" value={form.last_seen_date}
              onChange={(e) => setForm({ ...form, last_seen_date: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Last Seen Location *</label>
            <input
              type="text" value={form.last_seen_location}
              onChange={(e) => setForm({ ...form, last_seen_location: e.target.value })}
              placeholder="e.g. Near Kamrup Bridge, Assam"
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
            placeholder="Any additional details about the missing person..."
            className="w-full border rounded px-3 py-2"
          />
        </div>

        {/* Photo Upload */}
        <div>
          <label className="block text-sm font-medium mb-1">Photo of Missing Person</label>
          <div className="flex items-start gap-4">
            <label className="flex flex-col items-center justify-center w-32 h-32 border-2 border-dashed rounded-lg cursor-pointer hover:border-blue-400">
              <input type="file" accept="image/*" onChange={handlePhoto} className="hidden" />
              {preview ? (
                <img src={preview} alt="Preview" className="w-full h-full object-cover rounded-lg" />
              ) : (
                <span className="text-xs text-gray-400 text-center px-2">Click to upload photo</span>
              )}
            </label>
            {photo && (
              <div className="text-sm text-gray-600 pt-2">
                <p>{photo.name}</p>
                <p>{(photo.size / 1024).toFixed(0)} KB</p>
                <button onClick={() => { setPhoto(null); setPreview('') }} className="text-red-500 text-xs mt-1">Remove</button>
              </div>
            )}
          </div>
        </div>

        <button
          onClick={submit}
          disabled={submitting || !form.reporter_name || !form.phone || !form.missing_person_name || !form.last_seen_date || !form.last_seen_location}
          className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:opacity-50"
        >
          {submitting ? 'Filing...' : 'File Complaint'}
        </button>

        {msg && (
          <p className={`text-sm font-medium ${msg.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
            {msg}
          </p>
        )}
      </div>
    </div>
  )
}
