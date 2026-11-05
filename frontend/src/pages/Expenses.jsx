import { Fragment, useEffect, useState } from 'react'
import ExpenseForm from '../components/ExpenseForm'
import { apiFetch } from '../lib/api'
import { CATEGORIES, formatDate, formatMoney } from '../lib/utils'

export default function Expenses() {
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [category, setCategory] = useState('')
  const [merchant, setMerchant] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [openId, setOpenId] = useState(null)   // which row shows its items

  // Load the list again whenever a filter changes
  useEffect(() => {
    let ignore = false   // if the filter changes again before this answer arrives, throw this answer away
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (merchant.trim()) params.set('merchant', merchant.trim())

    apiFetch(`/expenses?${params}`)
      .then((data) => { if (!ignore) { setExpenses(data); setError('') } })
      .catch((err) => { if (!ignore) setError(err.message) })
      .finally(() => { if (!ignore) setLoading(false) })

    return () => { ignore = true }
  }, [category, merchant])

  const shownTotal = expenses.reduce((sum, expense) => sum + Number(expense.total), 0)

  function handleSaved(saved) {
    // add the new one and keep the list newest-first
    setExpenses([saved, ...expenses].sort((a, b) => b.expense_date.localeCompare(a.expense_date)))
    setShowForm(false)
  }

  async function handleDelete(expense) {
    if (!window.confirm(`Delete ${expense.merchant} (${formatMoney(expense.total)})?`)) return
    try {
      await apiFetch(`/expenses/${expense.id}`, { method: 'DELETE' })
      setExpenses(expenses.filter((e) => e.id !== expense.id))
    } catch (err) {
      alert(err.message)
    }
  }

  async function viewReceipt(id) {
    try {
      const { url } = await apiFetch(`/expenses/${id}/image`)   // a 1-hour private link
      window.open(url, '_blank', 'noopener')
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-xl font-bold mr-auto">Your expenses</h2>
        <input placeholder="Search merchant…" value={merchant} onChange={(ev) => setMerchant(ev.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 bg-white" />
        <select value={category} onChange={(ev) => setCategory(ev.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 bg-white">
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <button onClick={() => setShowForm(!showForm)}
          className="rounded-lg px-4 py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700">
          {showForm ? 'Close' : '+ Add expense'}
        </button>
      </div>

      {showForm && <ExpenseForm onSaved={handleSaved} onCancel={() => setShowForm(false)} />}

      {error && <p className="text-red-600">{error}</p>}

      <div className="bg-white rounded-2xl shadow overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-slate-50 text-sm text-slate-500">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Merchant</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3 text-right">Total</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((expense) => (
              <Fragment key={expense.id}>
                <tr onClick={() => setOpenId(openId === expense.id ? null : expense.id)}
                  className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer">
                  <td className="px-4 py-3 whitespace-nowrap">{formatDate(expense.expense_date)}</td>
                  <td className="px-4 py-3 font-medium">{expense.merchant}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold px-2 py-1">
                      {expense.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-semibold">{formatMoney(expense.total)}</td>
                  <td className="px-4 py-3 text-right whitespace-nowrap space-x-3 text-sm">
                    {expense.image_url && (
                      <button onClick={(ev) => { ev.stopPropagation(); viewReceipt(expense.id) }}
                        className="text-emerald-600 hover:underline">
                        Receipt
                      </button>
                    )}
                    <button onClick={(ev) => { ev.stopPropagation(); handleDelete(expense) }}
                      className="text-red-600 hover:underline">
                      Delete
                    </button>
                  </td>
                </tr>

                {openId === expense.id && (
                  <tr className="bg-slate-50">
                    <td colSpan={5} className="px-4 py-3 text-sm text-slate-600">
                      {expense.items.length === 0 ? 'No items recorded.' : (
                        <ul className="space-y-1 max-w-md">
                          {expense.items.map((item) => (
                            <li key={item.id} className="flex justify-between">
                              <span>{item.name}</span>
                              <span>{formatMoney(item.price)}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      {Number(expense.tax) > 0 && <p className="mt-2">Tax: {formatMoney(expense.tax)}</p>}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
        {loading && <p className="p-6 text-center text-slate-500">Loading…</p>}
        {!loading && expenses.length === 0 && <p className="p-6 text-center text-slate-500">No expenses found.</p>}
      </div>

      {expenses.length > 0 && (
        <p className="text-right text-slate-600">
          {expenses.length} expenses · Total <b>{formatMoney(shownTotal)}</b>
        </p>
      )}
    </div>
  )
}
