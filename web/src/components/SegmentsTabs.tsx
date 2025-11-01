import type { Segment } from '../lib/types'

export default function SegmentsTabs({ segments }: { segments: Segment[] }) {
  if (!segments?.length) return null
  const s = segments[0]
  return (
    <div className="space-y-2">
      <div className="flex gap-2 flex-wrap">
        <span className="chip">{s.name}</span>
      </div>
      <div className="grid md:grid-cols-3 gap-3">
        {s.buckets.map((b) => (
          <div key={b.label} className="card p-3">
            <div className="text-sm text-gray-300 mb-1">{b.label}</div>
            <Stacked label="A" a={b.A} b={b.B} t={b.tie} />
          </div>
        ))}
      </div>
    </div>
  )
}

function Stacked({ label, a, b, t }: { label: string; a: number; b: number; t: number }) {
  const A = Math.round(a * 100)
  const B = Math.round(b * 100)
  const T = Math.round(t * 100)
  const total = A + B + T || 1
  return (
    <div>
      <div className="w-full h-3 bg-[#1f232b] rounded-xl overflow-hidden flex">
        <div style={{ width: `${(A / total) * 100}%`, background: 'var(--brand)' }} />
        <div style={{ width: `${(B / total) * 100}%`, background: 'var(--brand2)' }} />
        <div style={{ width: `${(T / total) * 100}%`, background: '#2f3542' }} />
      </div>
      <div className="text-xs text-gray-400 mt-1">A {A}% • B {B}% • Tie {T}%</div>
    </div>
  )
}


