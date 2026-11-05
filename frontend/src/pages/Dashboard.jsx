import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { apiFetch } from '../lib/api'
import { formatMoney } from '../lib/utils'

const ACCENT = '#059669'   // emerald-600: the app's green, for "this month"
const MUTED = '#cbd5e1'    // slate-300: grey, for the other months
const INK = '#475569'      // slate-600: text colour for labels

// The last 6 months, oldest first: [{ key: "2026-06", label: "Jun" }, ...]
function lastSixMonths() {
  const now = new Date()
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - 5 + i, 1)
    return {
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('en-IN', { month: 'short' }),
    }
  })
}

// 1500 -> "₹1.5k" for the axis, where space is tight
function shortMoney(value) {
  return value >= 1000 ? `₹${Math.round(value / 100) / 10}k` : `₹${value}`
}

export default function Dashboard() {
  const [expenses, setExpenses] = useState(null)   // null = still loading
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    const start = `${lastSixMonths()[0].key}-01`     // only fetch the last 6 months
    apiFetch(`/expenses?start=${start}`)
      .then((data) => { if (!ignore) setExpenses(data) })
      .catch((err) => { if (!ignore) setError(err.message) })
    return () => { ignore = true }
  }, [])

  if (error) return <p className="text-red-600">{error}</p>
  if (!expenses) return <p className="mt-10 text-center text-slate-500">Loading…</p>

  // ---- Work out the numbers ----
  const months = lastSixMonths()
  const thisKey = months[5].key
  const lastKey = months[4].key

  const totals = Object.fromEntries(months.map((m) => [m.key, 0]))   // { "2026-06": 0, ... }
  for (const e of expenses) {
    const key = e.expense_date.slice(0, 7)                          // "2026-11-05" -> "2026-11"
    if (key in totals) totals[key] += Number(e.total)
  }
  const monthly = months.map((m) => ({ ...m, total: totals[m.key] }))

  const thisMonth = expenses.filter((e) => e.expense_date.startsWith(thisKey))
  const byCategory = {}
  for (const e of thisMonth) byCategory[e.category] = (byCategory[e.category] || 0) + Number(e.total)
  const categories = Object.entries(byCategory)
    .map(([category, total]) => ({ category, total }))
    .sort((a, b) => b.total - a.total)                              // biggest first

  const thisTotal = totals[thisKey]
  const lastTotal = totals[lastKey]
  const change = lastTotal > 0 ? Math.round(((thisTotal - lastTotal) / lastTotal) * 100) : null

  // ---- Draw ----
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Dashboard</h2>

      {/* Headline numbers */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatTile label={`This month (${months[5].label})`} value={formatMoney(thisTotal)}
          note={change === null ? 'No spending last month' : `${change > 0 ? '▲' : change < 0 ? '▼' : '='} ${Math.abs(change)}% vs ${months[4].label}`} />
        <StatTile label={`Last month (${months[4].label})`} value={formatMoney(lastTotal)} />
        <StatTile label="Expenses this month" value={thisMonth.length} />
        <StatTile label="Top category" value={categories[0]?.category ?? '-'}
          note={categories[0] ? formatMoney(categories[0].total) : 'Nothing yet'} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Spending per month */}
        <div className="bg-white rounded-2xl shadow p-5">
          <h3 className="font-bold">Spending per month</h3>
          <p className="text-sm text-slate-500 mb-3">Last 6 months · this month in green</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthly} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: INK, fontSize: 12 }} />
              <YAxis tickFormatter={shortMoney} tickLine={false} axisLine={false} width={56}
                tick={{ fill: INK, fontSize: 12 }} />
              <Tooltip cursor={{ fill: '#f1f5f9' }} formatter={(value) => [formatMoney(value), 'Spent']} />
              <Bar dataKey="total" radius={[4, 4, 0, 0]} maxBarSize={40}>
                {monthly.map((m) => <Cell key={m.key} fill={m.key === thisKey ? ACCENT : MUTED} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* This month by category */}
        <div className="bg-white rounded-2xl shadow p-5">
          <h3 className="font-bold">This month by category</h3>
          <p className="text-sm text-slate-500 mb-3">Biggest first</p>
          {categories.length === 0 ? (
            <p className="py-10 text-center text-slate-500">No spending this month yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(120, categories.length * 44)}>
              <BarChart data={categories} layout="vertical" margin={{ top: 0, right: 80, left: 0, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="category" tickLine={false} axisLine={false} width={100}
                  tick={{ fill: INK, fontSize: 13 }} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} formatter={(value) => [formatMoney(value), 'Spent']} />
                <Bar dataKey="total" fill={ACCENT} radius={[0, 4, 4, 0]} barSize={20}>
                  <LabelList dataKey="total" position="right" formatter={formatMoney} fill={INK} fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

function StatTile({ label, value, note }) {
  return (
    <div className="bg-white rounded-2xl shadow p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-800">{value}</p>
      {note && <p className="mt-1 text-sm text-slate-500">{note}</p>}
    </div>
  )
}
