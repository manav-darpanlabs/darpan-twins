import type { Drivers } from '../lib/types'

export default function EvidenceTrace({ drivers }: { drivers: Drivers }) {
  return (
    <details className="mt-2">
      <summary className="cursor-pointer text-sm text-gray-300">Evidence Trace</summary>
      <div className="grid md:grid-cols-2 gap-3 mt-2">
        <div className="card p-3">
          <div className="font-semibold mb-1">Price/Value</div>
          <div className="text-sm">Payable A ₹{drivers.price_value.payable_A} • B ₹{drivers.price_value.payable_B}</div>
          <div className="text-xs text-gray-400">Coupon usable: A {drivers.price_value.coupon_usable_A ? 'yes':'no'} • B {drivers.price_value.coupon_usable_B ? 'yes':'no'}</div>
        </div>
        <div className="card p-3">
          <div className="font-semibold mb-1">Delivery</div>
          <div className="text-sm">ETA p50 — A {drivers.delivery.eta_A_p50}m • B {drivers.delivery.eta_B_p50}m</div>
        </div>
        <div className="card p-3">
          <div className="font-semibold mb-1">Trust</div>
          <div className="text-sm">A {drivers.trust.rating_A} ({drivers.trust.reviews_A}) • B {drivers.trust.rating_B} ({drivers.trust.reviews_B})</div>
        </div>
        <div className="card p-3">
          <div className="font-semibold mb-1">Fit</div>
          <div className="text-sm">Cuisine match — A {(drivers.fit.cuisine_match_A*100).toFixed(0)}% • B {(drivers.fit.cuisine_match_B*100).toFixed(0)}%</div>
        </div>
      </div>
    </details>
  )
}


