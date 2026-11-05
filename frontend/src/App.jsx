function App() {
  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow p-8 text-center">
        <h1 className="text-3xl font-bold text-emerald-600">AI Expense Tracker</h1>
        <p className="mt-2 text-slate-500">Frontend is running 🎉</p>
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