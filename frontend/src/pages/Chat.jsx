import { useEffect, useRef, useState } from 'react'
import { apiFetch } from '../lib/api'

const SUGGESTIONS = [
  'How much have I spent this month?',
  'Am I spending more on food this month than last month?',
  'Am I over any budget?',
  'What was my biggest expense last month?',
]

export default function Chat() {
  const [messages, setMessages] = useState([])   // each one: { role: 'user' or 'model', text, steps }
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)                 // an invisible marker at the end of the chat

  // Scroll down whenever a new message appears
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  async function send(text) {
    const question = text.trim()
    if (!question || thinking) return

    // The server doesn't remember anything, so send the earlier messages along (just who said what)
    const history = messages.map((m) => ({ role: m.role, text: m.text }))

    setMessages([...messages, { role: 'user', text: question }])
    setInput('')
    setError('')
    setThinking(true)
    try {
      const reply = await apiFetch('/chat', { method: 'POST', body: { message: question, history } })
      setMessages((current) => [
        ...current,
        { role: 'model', text: reply.answer || "Sorry, I don't have an answer for that.", steps: reply.steps },
      ])
    } catch (err) {
      setMessages((current) => current.slice(0, -1))   // take the question back off...
      setInput(question)                               // ...and put it back in the box to try again
      setError(err.message)
    } finally {
      setThinking(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow flex flex-col h-[calc(100vh-8rem)]">
      {/* The conversation */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-8 space-y-4">
            <p className="text-4xl">🤖</p>
            <p className="text-slate-600">Ask me anything about your spending.</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm text-emerald-700 hover:bg-emerald-100">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
              m.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-800'
            }`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.steps?.length > 0 && <ToolSteps steps={m.steps} />}
            </div>
          </div>
        ))}

        {thinking && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-slate-100 px-4 py-2 text-slate-500">Thinking… 🤔</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* The input box */}
      {error && <p className="px-4 text-sm text-red-600">{error}</p>}
      <form onSubmit={(ev) => { ev.preventDefault(); send(input) }}
        className="border-t border-slate-200 p-3 flex gap-2">
        <input value={input} onChange={(ev) => setInput(ev.target.value)}
          placeholder="Ask about your spending…"
          className="flex-1 border border-slate-300 rounded-lg px-3 py-2 focus:outline-emerald-500" />
        <button type="submit" disabled={thinking || !input.trim()}
          className="rounded-lg px-4 py-2 font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50">
          Send
        </button>
      </form>
    </div>
  )
}

// The agent's "working out": which tools it called, with which inputs
function ToolSteps({ steps }) {
  return (
    <details className="mt-2 text-xs text-slate-500">
      <summary className="cursor-pointer select-none">
        🔧 Used {steps.length} tool{steps.length > 1 ? 's' : ''}
      </summary>
      <ol className="mt-1 ml-4 list-decimal space-y-1">
        {steps.map((step, i) => (
          <li key={i}>
            <span className={`font-semibold ${step.ok ? 'text-emerald-700' : 'text-red-600'}`}>{step.tool}</span>{' '}
            <code className="break-all">{JSON.stringify(step.args)}</code>
          </li>
        ))}
      </ol>
    </details>
  )
}
