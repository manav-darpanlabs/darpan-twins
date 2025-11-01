import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

export default function RunProgress() {
  const { id } = useParams()
  const nav = useNavigate()
  const location = useLocation() as any
  const sample = location?.state?.sample ?? 100

  const [done, setDone] = useState(0)
  const [votes, setVotes] = useState<string[]>([])

  useEffect(() => {
    const t = setInterval(() => {
      setDone(d => {
        const nd = Math.min(sample, d + Math.max(1, Math.round(sample/20)))
        const add = Array.from({ length: nd - d }).map(() => Math.random() < 0.5 ? 'A' : 'B')
        setVotes(v => [...v, ...add])
        if (nd >= sample) {
          clearInterval(t)
          setTimeout(() => nav(`/results/${id}`), 600)
        }
        return nd
      })
    }, 200)
    return () => clearInterval(t)
  }, [id, nav, sample])

  const pct = Math.round((done / sample) * 100)

  return (
    <main className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Running</h1>
      <p className="text-gray-300">Evaluating {sample} twins…</p>
      <div className="w-full h-3 bg-[#1f232b] rounded-xl overflow-hidden">
        <div className="h-full bg-[var(--brand2)]" style={{ width: `${pct}%` }} />
      </div>
      <div className="grid grid-cols-10 gap-2">
        {votes.slice(-50).map((v, i) => (
          <div key={i} className={`h-6 rounded-full ${v==='A'?'bg-[var(--brand)]':'bg-[var(--brand2)]'}`} />
        ))}
      </div>
      <button className="btn btn-secondary" onClick={() => nav(`/results/${id}`)}>Go to results when ready</button>
    </main>
  )
}


