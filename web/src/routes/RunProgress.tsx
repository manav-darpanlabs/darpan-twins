import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import AnimatedGradientBackground from '@/components/AnimatedGradientBackground'

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
    <div className="relative min-h-screen">
      {/* Animated gradient with dynamic intensity based on progress */}
      <AnimatedGradientBackground
        breathing={true}
        startingGap={100 + pct * 0.5}
        breathingRange={20}
        animationSpeed={0.002}
        gradientColors={[
          "#020617",   // Deep base
          "#C1E329",   // Brand yellow-green
          "#3fb1f0",   // Brand blue
          "#00F5A0",   // Neon green
          "#1a1d23",   // Panel blend
          "#00D9F5",   // Neon cyan
          "#0a0a0a"    // Deep black
        ]}
        gradientStops={[15, 30, 45, 60, 75, 88, 100]}
      />

      <motion.main
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative z-10 max-w-3xl mx-auto p-6 space-y-6">
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
    </motion.main>
    </div>
  )
}
