export default function WinBar({ A, B, tie }: { A: number; B: number; tie: number }) {
  const a = Math.round(A * 100)
  const b = Math.round(B * 100)
  const t = Math.round(tie * 100)
  const total = a + b + t || 1
  return (
    <div className="space-y-2">
      <div className="w-full h-5 bg-[#1f232b] rounded-xl overflow-hidden flex">
        <div style={{ width: `${(a / total) * 100}%`, background: 'var(--brand)' }} />
        <div style={{ width: `${(b / total) * 100}%`, background: 'var(--brand2)' }} />
        <div style={{ width: `${(t / total) * 100}%`, background: '#2f3542' }} />
      </div>
      <div className="flex gap-4 text-sm text-gray-300">
        <span>A: {a}%</span><span>B: {b}%</span><span>Tie: {t}%</span>
      </div>
    </div>
  )
}


