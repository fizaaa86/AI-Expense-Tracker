import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL

// Call our FastAPI backend with the logged-in user's token attached.
// Usage:  apiFetch('/expenses')   or   apiFetch('/budgets', { method: 'PUT', body: {...} })
export async function apiFetch(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()

  const headers = { ...options.headers }
  if (session) headers.Authorization = `Bearer ${session.access_token}`

  let body = options.body
  if (body && !(body instanceof FormData)) {   // plain objects are sent as JSON
    body = JSON.stringify(body)
    headers['Content-Type'] = 'application/json'
  }

    let response
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers, body })
  } catch {
    // No answer at all: the backend isn't running, or it crashed (the real error is in its terminal)
    throw new Error('Could not reach the server. Is the backend running? If so, check its terminal for an error.')
  }


  if (!response.ok) {
    // FastAPI puts the reason in "detail", for example "Expense not found"
    const data = await response.json().catch(() => ({}))
    const detail = typeof data.detail === 'string'
      ? data.detail
      : Array.isArray(data.detail)
        ? data.detail.map((d) => d.msg).join('; ')   // Pydantic's list of problems
        : JSON.stringify(data.detail ?? data)

    throw new Error(detail || `Request failed (${response.status})`)
  }
  if (response.status === 204) return null   // e.g. DELETE returns no body
  return response.json()
}
