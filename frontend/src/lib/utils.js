// The same categories Gemini chooses from (schemas.py), so budgets always match
export const CATEGORIES = [
  'Food', 'Groceries', 'Transport', 'Shopping', 'Bills', 'Health', 'Entertainment', 'Other',
]

const rupees = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })

// 1227.5 -> "₹1,227.50"
export function formatMoney(amount) {
  return rupees.format(Number(amount))
}

// "2026-11-05" -> "5 Nov 2026"
export function formatDate(isoDate) {
  return new Date(`${isoDate}T00:00`).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

// Today as "YYYY-MM-DD" in YOUR time zone
export function todayLocal() {
  return new Date().toLocaleDateString('en-CA')
}
