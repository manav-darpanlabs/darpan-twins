import { useNavigate } from 'react-router-dom'
import { useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedGradientBackground from '@/components/AnimatedGradientBackground'

export default function ExperimentForm() {
  const nav = useNavigate()
  const [city, setCity] = useState('')
  const [cardA, setCardA] = useState<File | null>(null)
  const [cardB, setCardB] = useState<File | null>(null)
  const [name, setName] = useState('City AB Test')
  const [sample, setSample] = useState(100)

  const ready = useMemo(() => city && cardA && cardB, [city, cardA, cardB])

  function start() {
    const id = `EXP-${new Date().toISOString().slice(0,10)}-${Math.floor(Math.random()*1000).toString().padStart(3,'0')}`
    nav(`/run/${id}`, { state: { name, city, sample } })
  }

  return (
    <div className="relative min-h-screen">
      {/* Animated gradient background with subtle settings */}
      <AnimatedGradientBackground
        breathing={true}
        startingGap={150}
        breathingRange={15}
        animationSpeed={0.001}
        gradientColors={[
          "#020617",   // Deep base
          "#00F5A0",   // Neon green
          "#00D9F5",   // Neon cyan
          "#1a1d23",   // Panel color blend
          "#22C55E",   // Vivid green
          "#3fb1f0",   // Brand blue
          "#0a0a0a"    // Deep black
        ]}
        gradientStops={[20, 35, 50, 65, 75, 85, 100]}
      />

      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 max-w-6xl mx-auto p-6 space-y-6">
      <section className="space-y-1">
        <h1 className="text-3xl font-bold">Create an experiment</h1>
        <p className="text-gray-300 max-w-2xl">Select the city, upload two restaurant cards, and specify context. We’ll ask your customer twins to choose A or B and explain why.</p>
      </section>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-4 space-y-3">
          <label className="text-sm text-gray-300">Experiment name</label>
          <input className="w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2" value={name} onChange={e=>setName(e.target.value)} />

          <label className="text-sm text-gray-300">City</label>
          <input placeholder="Mumbai" className="w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2" value={city} onChange={e=>setCity(e.target.value)} />

          <label className="text-sm text-gray-300">Twin sample size</label>
          <input type="number" min={10} max={1000} className="w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2" value={sample} onChange={e=>setSample(parseInt(e.target.value||'0'))} />
        </div>

        <div className="card p-4 space-y-3">
          <div>
            <label className="text-sm text-gray-300">Card A (PNG/JPG)</label>
            <input type="file" accept="image/*" onChange={e=>setCardA(e.target.files?.[0]||null)} />
          </div>
          <div>
            <label className="text-sm text-gray-300">Card B (PNG/JPG)</label>
            <input type="file" accept="image/*" onChange={e=>setCardB(e.target.files?.[0]||null)} />
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button className={`btn ${ready? 'btn-primary':'opacity-50 cursor-not-allowed btn-primary'}`} onClick={start} disabled={!ready}>Start experiment</button>
      </div>
    </motion.main>
    </div>
  )
}
