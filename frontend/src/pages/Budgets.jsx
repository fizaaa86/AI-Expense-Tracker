import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/api'
import { CATEGORIES, formatMoney } from '../lib/utils'

const thisMonth = new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })

// green when fine, orange when close, red when over
function barColour(percent, over) {
  if (over) return 'bg-red-500'
  if (percent >= 80) return 'bg-amber-500'
  return 'bg-emerald-500'
}

export default function Budgets() {
  const [statuses, setStatuses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [category, setCategory] = useState(CATEGORIES[0])
  const [limit, setLimit] = useState('')
  const [saving, setSaving] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)   // change it to load the list again

  useEffect(() => {
    let ignore = false
    apiFetch('/budgets/status')
      .then((data) => { if (!ignore) { setStatuses(data); setError('') } })
      .catch((err) => { if (!ignore) setError(err.message) })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [reloadKey])

  async function handleSave(ev) {
    ev.preventDefault()
    setSaving(true)
    setError('')
    try {
      await apiFetch('/budgets', { method: 'PUT', body: { category, monthly_limit: limit } })
      setLimit('')
      setReloadKey((k) => k + 1)   // reload, so "spent" is worked out by the backend
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(status) {
    if (!window.confirm(`Remove the ${status.category} budget?`)) return
    try {
      await apiFetch(`/budgets/${status.id}`, { method: 'DELETE' })
      setStatuses(statuses.filter((s) => s.id !== status.id))
    } catch (err) {
      alert(err.message)
    }
  }

  function startEdit(status) {
    setCategory(status.category)
    setLimit(status.monthly_limit)
  }

  const overCount = statuses.filter((s) => s.over_budget).length

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline gap-2">
        <h2 className="text-xl font-bold mr-auto">Budgets for {thisMonth}</h2>
        {statuses.length > 0 && (
          <p className={`text-sm font-semibold ${overCount ? 'text-red-600' : 'text-emerald-700'}`}>
            {overCount ? `${overCount} over budget` : 'All within budget 👍'}
          </p>
        )}
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-2xl shadow p-4 flex flex-wrap items-end gap-3">
        <label className="block">
          <span className="text-sm text-slate-600">Category</span>
          <select value={category} onChange={(ev) => setCategory(ev.target.value)}
            className="block border border-slate-300 rounded-lg px-3 py-2 bg-white">
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Monthly limit (₹)</span>
          <input type="number" required min="1" step="0.01" value={limit}
            onChange={(ev) => setLimit(ev.target.value)}
            className="block border border-slate-300 rounded-lg px-3 py-2 w-40" />
        </label>
        <button type="submit" disabled={saving}
          className="rounded-lg px-4 py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50">
          {saving ? 'Saving…' : 'Save budget'}
        </button>
      </form>

      {error && <p className="text-red-600">{error}</p>}
      {loading && <p className="text-center text-slate-500">Loading…</p>}
      {!loading && statuses.length === 0 && (
        <p className="text-center text-slate-500">No budgets yet. Set one above.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {statuses.map((s) => {
          const percent = Math.min(100, (Number(s.spent) / Number(s.monthly_limit)) * 100)
          return (
            <div key={s.id} className="bg-white rounded-2xl shadow p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold">{s.category}</h3>
                {s.over_budget && (
                  <span className="rounded-full bg-red-100 text-red-700 text-xs font-semibold px-2 py-1">
                    Over budget
                  </span>
                )}
              </div>

              <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
                <div className={`h-full rounded-full ${barColour(percent, s.over_budget)}`}
                  style={{ width: `${percent}%` }} />
              </div>

              <p className="text-sm text-slate-600">
                {formatMoney(s.spent)} of {formatMoney(s.monthly_limit)}
              </p>
              <p className={`text-sm font-semibold ${s.over_budget ? 'text-red-600' : 'text-emerald-700'}`}>
                {s.over_budget
                  ? `Over by ${formatMoney(-Number(s.remaining))}`
                  : `${formatMoney(s.remaining)} left`}
              </p>

              <div className="flex gap-3 text-sm">
                <button onClick={() => startEdit(s)} className="text-emerald-600 hover:underline">Edit</button>
                <button onClick={() => handleDelete(s)} className="text-red-600 hover:underline">Remove</button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
