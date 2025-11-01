import type { Reason } from '../lib/types'

export default function TopReasons({ reasons }: { reasons: Reason[] }) {
  return (
    <ul className="list-disc pl-5 space-y-2">
      {reasons.map((r, i) => (
        <li key={i}>
          <span className="chip mr-2">{r.driver}</span>
          {r.summary}
          <span className="ml-2 text-xs text-gray-400">{r.evidence.map((e) => (
            <span key={e} className="chip mr-1">{e}</span>
          ))}</span>
        </li>
      ))}
    </ul>
  )
}


