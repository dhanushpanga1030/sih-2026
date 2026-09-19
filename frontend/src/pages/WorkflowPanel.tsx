import { useEffect, useState } from 'react'

const STATE_COLORS: Record<string, string> = {
  ai_recommendation: 'bg-navy-500/20 text-navy-500 dark:text-navy-300',
  officer_review: 'bg-accent/20 text-accent',
  approved: 'bg-emerald-500/20 text-emerald-400',
  rejected: 'bg-red-500/20 text-red-400',
  modified: 'bg-orange-500/20 text-orange-400',
  in_progress: 'bg-purple-500/20 text-purple-400',
  completed: 'bg-emerald-500/30 text-emerald-300',
  cancelled: 'bg-slate-500/20 text-slate-400',
}

const VALID_TRANSITIONS: Record<string, string[]> = {
  ai_recommendation: ['officer_review', 'approved', 'rejected'],
  officer_review: ['approved', 'rejected', 'modified'],
  modified: ['officer_review', 'approved'],
  approved: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
  rejected: ['ai_recommendation'],
  completed: [],
  cancelled: ['ai_recommendation'],
}

export default function WorkflowPanel() {
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newType, setNewType] = useState('risk_assessment')
  const [newHab, setNewHab] = useState('')

  const loadItems = () => {
    fetch('/api/workflow/list').then(r => r.json()).then(d => { setItems(d); setLoading(false) })
    fetch('/api/workflow/stats').then(r => r.json()).then(setStats)
  }

  useEffect(loadItems, [])

  const transition = async (id: string, newState: string) => {
    await fetch('/api/workflow/transition', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: id, new_state: newState, actor: 'officer', note: '' }),
    })
    loadItems()
  }

  const createItem = async () => {
    if (!newHab) return
    await fetch(`/api/workflow/create?item_type=${newType}&habitation=${encodeURIComponent(newHab)}`, { method: 'POST' })
    setShowCreate(false)
    setNewHab('')
    loadItems()
  }

  if (loading) return (
    <div className="py-20 text-center">
      <div className="inline-flex items-center gap-3 glass-card px-6 py-4">
        <div className="w-5 h-5 border-2 border-navy-400 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Loading workflow...</span>
      </div>
    </div>
  )

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #106EAB, #79C5DC)' }}>
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>Government Workflow</h1>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Approval pipeline and state machine</p>
          </div>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="glass-pill px-4 py-2 text-sm font-medium transition-colors" style={{ color: 'var(--color-primary)' }}>
          + New Item
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass-card p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Total</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{stats.total}</div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Pending Review</div>
            <div className="text-xl font-bold text-accent">{stats.pending_review}</div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Completed</div>
            <div className="text-xl font-bold text-emerald-400">{stats.completed}</div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>States Active</div>
            <div className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>{Object.keys(stats.by_state || {}).length}</div>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="glass-card p-5 space-y-3">
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Type</label>
              <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}>
                <option value="risk_assessment">Risk Assessment</option>
                <option value="relocation_plan">Relocation Plan</option>
                <option value="emergency_response">Emergency Response</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Habitation</label>
              <input value={newHab} onChange={e => setNewHab(e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} placeholder="Habitation name" />
            </div>
            <div className="flex items-end">
              <button onClick={createItem} className="text-white px-4 py-2 rounded-lg text-sm font-medium transition-all" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>Create</button>
            </div>
          </div>
        </div>
      )}

      <div className="glass-card p-5">
        <h2 className="font-semibold mb-4" style={{ color: 'var(--color-text)' }}>Workflow Items</h2>
        {items.length === 0 ? (
          <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No workflow items. Create one to start the approval process.</p>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <div key={item.item_id} className="rounded-xl p-4 space-y-3" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>{item.item_id}</span>
                    <span className="font-medium" style={{ color: 'var(--color-text)' }}>{item.habitation}</span>
                    <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{item.item_type}</span>
                  </div>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${STATE_COLORS[item.state] || 'bg-slate-500/20 text-slate-400'}`}>
                    {item.state.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex gap-2">
                  {(VALID_TRANSITIONS[item.state] || []).map(s => (
                    <button
                      key={s}
                      onClick={() => transition(item.item_id, s)}
                      className="text-xs px-3 py-1.5 rounded-lg border transition-colors"
                      style={{ background: 'var(--color-surface-alt)', borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}
                    >
                      → {s.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
                {item.history && item.history.length > 1 && (
                  <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    Last: {item.history[item.history.length - 1].note || item.history[item.history.length - 1].state} — {item.history[item.history.length - 1].actor}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
