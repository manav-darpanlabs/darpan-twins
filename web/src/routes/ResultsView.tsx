import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ExperimentResult } from '../lib/types'
import WinBar from '../components/WinBar'
import TopReasons from '../components/TopReasons'
import SegmentsTabs from '../components/SegmentsTabs'
import EvidenceTrace from '../components/EvidenceTrace'
import { copyMarkdownSummary } from '../lib/summary'
import DriverCards from '../components/DriverCards'
import AnimatedGradientBackground from '@/components/AnimatedGradientBackground'

export default function ResultsView() {
  const [data, setData] = useState<ExperimentResult | null>(null)

  useEffect(() => {
    fetch('/mock/result.json').then(r=>r.json()).then(setData)
  }, [])

  if (!data) {
    return (
      <div className="relative min-h-screen">
        <AnimatedGradientBackground
          breathing={true}
          startingGap={120}
          breathingRange={30}
          animationSpeed={0.003}
        />
        <main className="relative z-10 max-w-6xl mx-auto p-6">Loading…</main>
      </div>
    )
  }

  // Dynamic gradient colors based on results
  const winnerColors = data.aggregate.A > data.aggregate.B
    ? ["#020617", "#C1E329", "#22C55E", "#00F5A0", "#1a1d23", "#38BDF8", "#0a0a0a"]  // Green-dominant for A
    : ["#020617", "#3fb1f0", "#00D9F5", "#0EA5E9", "#1a1d23", "#A855F7", "#0a0a0a"]  // Blue-dominant for B

  return (
    <div className="relative min-h-screen">
      <AnimatedGradientBackground
        breathing={true}
        startingGap={130}
        breathingRange={10}
        animationSpeed={0.0015}
        gradientColors={winnerColors}
        gradientStops={[10, 25, 40, 55, 70, 85, 100]}
      />

      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-6xl mx-auto p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Experiment Results</h1>
          <div className="mt-1 flex flex-wrap gap-2">
            <span className="chip">{data.city}</span>
            <span className="chip">Sample {data.sample_n}</span>
            <span className="chip">Confidence {data.aggregate.confidence}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <a className="btn btn-secondary" href={`about:blank?title=${encodeURIComponent('Create Jira tasks for '+data.experiment_id)}`} target="_blank" rel="noreferrer">Create Jira Tasks</a>
          <a className="btn btn-secondary" href={`about:blank`} target="_blank" rel="noreferrer">Share to Figma</a>
          <button className="btn btn-primary" onClick={() => navigator.clipboard.writeText(copyMarkdownSummary(data))}>Copy summary</button>
        </div>
      </header>

      <section className="card p-4 space-y-2">
        <h2 className="text-xl font-semibold mb-2">Aggregate results</h2>
        <WinBar A={data.aggregate.A} B={data.aggregate.B} tie={data.aggregate.tie} />
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <h3 className="font-semibold mb-2">Top reasons</h3>
          <TopReasons reasons={data.top_reasons} />
          <EvidenceTrace drivers={data.drivers} />
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-2">Recommended actions</h3>
          <ul className="list-disc pl-5 space-y-1">
            {data.recommended_actions.map((x,i)=>(<li key={i}>{x}</li>))}
          </ul>
        </div>
      </section>

      <section className="card p-4">
        <h3 className="font-semibold mb-2">Segments</h3>
        <SegmentsTabs segments={data.segments} />
      </section>

      <DriverCards d={data.drivers} />

      <section className="card p-4">
        <h3 className="font-semibold mb-2">Per-twin console</h3>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-gray-300">
              <tr><th className="text-left p-2">Twin</th><th className="text-left p-2">Winner</th><th className="text-left p-2">Reason</th></tr>
            </thead>
            <tbody>
              {data.twins.map((t,i)=>(
                <tr key={i} className="border-t border-[#232838]"><td className="p-2">{t.id}</td><td className="p-2">{t.winner}</td><td className="p-2">{t.reason}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </motion.main>
    </div>
  )
}
