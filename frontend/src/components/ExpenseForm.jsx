import { useState } from 'react'
import { apiFetch } from '../lib/api'
import { CATEGORIES, formatMoney, todayLocal } from '../lib/utils'

const inputClass = 'border border-slate-300 rounded-lg px-3 py-2 focus:outline-emerald-500'

// A form that saves an expense. `initial` can pre-fill it (the scan page will use this in 7d).
export default function ExpenseForm({ initial = {}, imagePath = null, onSaved, onCancel }) {
  const [merchant, setMerchant] = useState(initial.merchant ?? '')
  const [expenseDate, setExpenseDate] = useState(initial.expense_date ?? todayLocal())
  const [total, setTotal] = useState(initial.total ?? '')
  const [tax, setTax] = useState(initial.tax ?? '')
  const [category, setCategory] = useState(initial.category ?? 'Other')
  const [items, setItems] = useState(initial.items ?? [])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const itemsSum = items.reduce((sum, item) => sum + (Number(item.price) || 0), 0)

  // Change one field of one item row, keep the rest as they are
  function updateItem(index, field, value) {
    setItems(items.map((item, i) => (i === index ? { ...item, [field]: value } : item)))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const saved = await apiFetch('/expenses', {
        method: 'POST',
        body: {
          merchant,
          expense_date: expenseDate,
          total,
          tax: tax || 0,
          category,
          items: items
            .filter((item) => item.name.trim())   // skip empty rows
            .map((item) => ({ name: item.name, price: item.price || 0 })),
          image_url: imagePath,
        },
      })
      onSaved(saved)   // tell the parent page it worked
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow p-6 space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-sm text-slate-600">Merchant</span>
          <input required value={merchant} onChange={(ev) => setMerchant(ev.target.value)}
            className={`${inputClass} w-full`} />
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Date</span>
          <input type="date" required value={expenseDate} onChange={(ev) => setExpenseDate(ev.target.value)}
            className={`${inputClass} w-full`} />
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Total (₹)</span>
          <input type="number" required min="0.01" step="0.01" value={total}
            onChange={(ev) => setTotal(ev.target.value)} className={`${inputClass} w-full`} />
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Tax (₹)</span>
          <input type="number" min="0" step="0.01" value={tax} placeholder="0"
            onChange={(ev) => setTax(ev.target.value)} className={`${inputClass} w-full`} />
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Category</span>
          <select value={category} onChange={(ev) => setCategory(ev.target.value)}
            className={`${inputClass} w-full bg-white`}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Items (optional)</span>
          <button type="button" onClick={() => setItems([...items, { name: '', price: '' }])}
            className="text-sm text-emerald-600 font-semibold hover:underline">
            + Add item
          </button>
        </div>
        <div className="mt-2 space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex gap-2">
              <input placeholder="Item name" value={item.name}
                onChange={(ev) => updateItem(i, 'name', ev.target.value)} className={`${inputClass} flex-1`} />
              <input type="number" step="0.01" placeholder="Price" value={item.price}
                onChange={(ev) => updateItem(i, 'price', ev.target.value)} className={`${inputClass} w-32`} />
              <button type="button" aria-label="Remove item"
                onClick={() => setItems(items.filter((_, j) => j !== i))}
                className="px-2 text-slate-400 hover:text-red-600">
                ✕
              </button>
            </div>
          ))}
        </div>
        {items.length > 0 && (
          <p className="mt-2 text-sm text-slate-500">Items add up to {formatMoney(itemsSum)}</p>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel}
            className="rounded-lg px-4 py-2 font-semibold bg-slate-200 hover:bg-slate-300">
            Cancel
          </button>
        )}
        <button type="submit" disabled={saving}
          className="rounded-lg px-4 py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50">
          {saving ? 'Saving…' : 'Save expense'}
        </button>
      </div>
    </form>
  )
}
