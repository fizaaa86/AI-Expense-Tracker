import { useState } from 'react'
import ExpenseForm from '../components/ExpenseForm'
import { apiFetch } from '../lib/api'
import { formatDate, formatMoney } from '../lib/utils'

const MAX_SIZE = 5 * 1024 * 1024   // same 5 MB limit as the backend

// Turn Gemini's reading into starting values for the form
function toFormValues(receipt) {
  const items = receipt.items.map((item) => ({ name: item.name, price: item.price }))
  // Our expenses have no "discount" field, so keep it as a minus line: the items then add up to the total
  if (receipt.discount > 0) items.push({ name: 'Discount', price: -receipt.discount })
  return {
    merchant: receipt.merchant,
    expense_date: receipt.expense_date,
    total: receipt.total,
    tax: receipt.tax,
    category: receipt.category,
    items,
  }
}

export default function Scan({ onViewExpenses }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)   // a temporary link to show the photo on the page
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)     // what /receipts/scan sent back
  const [saved, setSaved] = useState(null)       // the expense, once saved

  function handleFile(ev) {
    const chosen = ev.target.files[0]
    if (preview) URL.revokeObjectURL(preview)    // free the old preview's memory
    setFile(chosen || null)
    setPreview(chosen ? URL.createObjectURL(chosen) : null)
    setResult(null)
    setError('')
  }

  async function handleScan() {
    if (file.size > MAX_SIZE) {
      setError('This image is larger than 5 MB. Please choose a smaller one.')
      return
    }
    setScanning(true)
    setError('')
    setResult(null)

    const formData = new FormData()   // how browsers send files
    formData.append('file', file)     // "file" = the parameter name in routers/receipts.py
    try {
      setResult(await apiFetch('/receipts/scan', { method: 'POST', body: formData }))
    } catch (err) {
      setError(err.message)
    } finally {
      setScanning(false)
    }
  }

  function reset() {
    if (preview) URL.revokeObjectURL(preview)
    setFile(null)
    setPreview(null)
    setResult(null)
    setSaved(null)
    setError('')
  }

  if (saved) {
    return (
      <div className="bg-white rounded-2xl shadow p-8 text-center space-y-4 max-w-md mx-auto">
        <p className="text-4xl">✅</p>
        <h2 className="text-xl font-bold">Saved!</h2>
        <p className="text-slate-600">
          {saved.merchant} · {formatMoney(saved.total)} on {formatDate(saved.expense_date)}
        </p>
        <div className="flex justify-center gap-2">
          <button onClick={reset}
            className="rounded-lg px-4 py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700">
            Scan another
          </button>
          <button onClick={onViewExpenses}
            className="rounded-lg px-4 py-2 font-semibold bg-slate-200 hover:bg-slate-300">
            View expenses
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2 items-start">
      {/* Left: choose and preview the photo */}
      <div className="bg-white rounded-2xl shadow p-6 space-y-4">
        <h2 className="text-xl font-bold">Scan a receipt</h2>
        <input type="file" accept="image/*" onChange={handleFile}
          className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-emerald-50 file:px-4 file:py-2 file:font-semibold file:text-emerald-700 hover:file:bg-emerald-100" />
        {preview && (
          <img src={preview} alt="Your receipt" className="max-h-96 mx-auto rounded-lg border border-slate-200" />
        )}
        <button onClick={handleScan} disabled={!file || scanning}
          className="w-full rounded-lg py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50">
          {scanning ? 'Gemini is reading your receipt…' : 'Read receipt with AI'}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {/* Right: the checks, warnings and the pre-filled form */}
      {result && (
        <div className="space-y-4">
          {result.validation.ok ? (
            <div className="rounded-xl bg-emerald-50 text-emerald-800 p-4 text-sm">
              ✅ The numbers add up{result.attempts === 2 && ' (Gemini needed a second look)'}.
              Check the details and save.
            </div>
          ) : (
            <div className="rounded-xl bg-amber-50 text-amber-800 p-4 text-sm">
              <p className="font-semibold">⚠️ Please check these before saving:</p>
              <ul className="list-disc ml-5 mt-1">
                {result.validation.problems.map((problem) => <li key={problem}>{problem}</li>)}
              </ul>
            </div>
          )}

          {result.possible_duplicates.length > 0 && (
            <div className="rounded-xl bg-red-50 text-red-800 p-4 text-sm">
              <p className="font-semibold">🔁 This looks like a bill you already saved:</p>
              <ul className="list-disc ml-5 mt-1">
                {result.possible_duplicates.map((dup) => (
                  <li key={dup.id}>{dup.merchant} · {formatMoney(dup.total)} on {formatDate(dup.expense_date)}</li>
                ))}
              </ul>
              <p className="mt-1">Only save it again if it really is a second purchase.</p>
            </div>
          )}

          <ExpenseForm
            key={result.image_path}
            initial={toFormValues(result.receipt)}
            imagePath={result.image_path}
            onSaved={setSaved}
            onCancel={reset}
          />
        </div>
      )}
    </div>
  )
}

/*URL.createObjectURL(file) makes a temporary link to the photo on your own computer, so you can preview it before anything is uploaded. revokeObjectURL throws that link away when it's no longer needed
FormData is how browsers send files. It's the same thing the Choose file button did in /docs. Our apiFetch already knows not to turn it into JSON.
toFormValues translates Gemini's reading into the form's starting values. The discount becomes a minus line ("Discount −₹72"). That way the items you save still add up to the total.
imagePath={result.image_path}: the photo was already stored during the scan, so saving just links the expense to it. That's how the Receipt button in your table works.
key={result.image_path} is a useful React trick. A form only reads initial when it first appears. Giving it a new key for each scan tells React "this is a brand-new form", so a second scan fills in fresh values instead of keeping the old ones.
if (saved) return ...: once you save, the page shows a success card instead of the form.
*/