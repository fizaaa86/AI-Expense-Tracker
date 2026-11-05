import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Login() {
  const [mode, setMode] = useState('signin')   // 'signin' or 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()   // stop the browser reloading the page
    setBusy(true)
    setError('')
    setMessage('')

    const { data, error } = mode === 'signin'
      ? await supabase.auth.signInWithPassword({ email, password })
      : await supabase.auth.signUp({ email, password })

    setBusy(false)
    if (error) setError(error.message)
    else if (mode === 'signup' && !data.session) {
      setMessage('Account created! Check your email to confirm it, then sign in.')
    }
    // On success there's nothing else to do: App.jsx notices the login and switches screens
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow p-8 w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-emerald-600 text-center">AI Expense Tracker</h1>
        <p className="text-center text-slate-500">
          {mode === 'signin' ? 'Sign in to your account' : 'Create a new account'}
        </p>

        <input
          type="email" required placeholder="Email"
          value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-emerald-500"
        />
        <input
          type="password" required minLength={6} placeholder="Password"
          value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-emerald-500"
        />

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {message && <p className="text-emerald-700 text-sm">{message}</p>}

        <button
          type="submit" disabled={busy}
          className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold rounded-lg py-2"
        >
          {busy ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Sign up'}
        </button>

        <p className="text-center text-sm text-slate-500">
          {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
            className="text-emerald-600 font-semibold hover:underline"
          >
            {mode === 'signin' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </form>
    </div>
  )
}
