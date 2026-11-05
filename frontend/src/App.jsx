import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import Login from './pages/Login'
import Expenses from './pages/Expenses'
import Scan from './pages/Scan'
import Budgets from './pages/Budgets'
const TABS = [
  { id: 'expenses', label: 'Expenses' },
  { id: 'scan', label: 'Scan receipt' },
  { id: 'budgets', label: 'Budgets' },
  { id: 'chat', label: 'Ask AI' },
]

function App() {
  const [session, setSession] = useState(undefined)   // undefined = still checking

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
    })
    return () => subscription.unsubscribe()
  }, [])

  if (session === undefined) return null
  if (!session) return <Login />
  return <Layout email={session.user.email} />
}

function Layout({ email }) {
  const [tab, setTab] = useState('expenses')

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-3 flex flex-wrap items-center gap-4">
          <h1 className="text-lg font-bold text-emerald-600">AI Expense Tracker</h1>
          <nav className="flex gap-1">
            {TABS.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
                  tab === t.id ? 'bg-emerald-100 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'
                }`}>
                {t.label}
              </button>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-slate-500">{email}</span>
            <button onClick={() => supabase.auth.signOut()}
              className="rounded-lg px-3 py-1.5 font-semibold bg-slate-200 hover:bg-slate-300">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-4">
        {tab === 'expenses' && <Expenses />}
        {tab === 'scan' && <Scan onViewExpenses={() => setTab('expenses')} />}
        {tab === 'budgets' && <Budgets />}
        {tab === 'chat' && <p className="mt-10 text-center text-slate-500">Coming in the next step 🚧</p>}


      </main>
    </div>
  )
}

export default App
