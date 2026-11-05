import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import { apiFetch } from './lib/api'
import Login from './pages/Login'

function App() {
  const [session, setSession] = useState(undefined)   // undefined = still checking

  useEffect(() => {
    // Already logged in from last time? (Supabase remembers it in the browser)
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    // ...and update whenever the user logs in or out
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
    })
    return () => subscription.unsubscribe()   // tidy up if App is ever removed
  }, [])

  if (session === undefined) return null   // a split second while checking
  if (!session) return <Login />
  return <Home email={session.user.email} />
}

// Temporary home screen: proves the backend accepts our token. We'll replace it in 7c.
function Home({ email }) {
  const [me, setMe] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    apiFetch('/me').then(setMe).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow p-8 text-center space-y-3">
        <h1 className="text-2xl font-bold text-emerald-600">Welcome!</h1>
        <p className="text-slate-600">Signed in as <b>{email}</b></p>
        {me && <p className="text-sm text-slate-500">Backend says your id is <code>{me.id}</code> ✅</p>}
        {error && <p className="text-sm text-red-600">Backend error: {error}</p>}
        <button
          onClick={() => supabase.auth.signOut()}
          className="bg-slate-200 hover:bg-slate-300 rounded-lg px-4 py-2 font-semibold"
        >
          Sign out
        </button>
      </div>
    </div>
  )
}

export default App


/*A component is just a function that returns what to show. The HTML-like part is called JSX.
In JSX it's className instead of HTML's class.
The class names are Tailwind:
min-h-screen: the page is at least the full screen height
flex items-center justify-center: centre the content
bg-white rounded-2xl shadow p-8: a white card with round corners, a shadow and padding
text-3xl font-bold text-emerald-600: big, bold, green text*/