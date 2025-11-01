import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Drivers } from '../lib/types'

export default function DriverCards({ d }: { d: Drivers }) {
  const priceData = [
    { name: 'A', payable: d.price_value.payable_A },
    { name: 'B', payable: d.price_value.payable_B },
  ]
  const etaData = [
    { name: 'A', eta: d.delivery.eta_A_p50 },
    { name: 'B', eta: d.delivery.eta_B_p50 },
  ]
  const trustData = [
    { name: 'A', rating: d.trust.rating_A, reviews: d.trust.reviews_A },
    { name: 'B', rating: d.trust.rating_B, reviews: d.trust.reviews_B },
  ]
  const fitData = [
    { name: 'A', match: Math.round(d.fit.cuisine_match_A * 100) },
    { name: 'B', match: Math.round(d.fit.cuisine_match_B * 100) },
  ]

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <Card title="Price / Value" subtitle={`Coupon usable: A ${d.price_value.coupon_usable_A ? 'yes':'no'} • B ${d.price_value.coupon_usable_B ? 'yes':'no'}`}>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={priceData}>
            <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#9aa3b2" />
            <YAxis stroke="#9aa3b2" />
            <Tooltip contentStyle={{ background: '#1a1d23', border: '1px solid #2a2f3a' }} />
            <Bar dataKey="payable" fill="var(--brand)" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Delivery time" subtitle="ETA p50 (minutes)">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={etaData}>
            <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#9aa3b2" />
            <YAxis stroke="#9aa3b2" />
            <Tooltip contentStyle={{ background: '#1a1d23', border: '1px solid #2a2f3a' }} />
            <Bar dataKey="eta" fill="var(--brand2)" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Trust" subtitle="Rating × Reviews">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={trustData}>
            <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#9aa3b2" />
            <YAxis yAxisId="left" stroke="#9aa3b2" />
            <YAxis yAxisId="right" orientation="right" stroke="#9aa3b2" />
            <Tooltip contentStyle={{ background: '#1a1d23', border: '1px solid #2a2f3a' }} />
            <Bar yAxisId="left" dataKey="rating" fill="var(--brand)" radius={6} />
            <Bar yAxisId="right" dataKey="reviews" fill="var(--brand2)" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Preference fit" subtitle="Cuisine match (%)">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={fitData}>
            <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#9aa3b2" />
            <YAxis stroke="#9aa3b2" />
            <Tooltip contentStyle={{ background: '#1a1d23', border: '1px solid #2a2f3a' }} />
            <Bar dataKey="match" fill="var(--brand)" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <div className="font-semibold">{title}</div>
      {subtitle ? <div className="text-sm text-gray-300 mb-2">{subtitle}</div> : null}
      {children}
    </div>
  )
}


