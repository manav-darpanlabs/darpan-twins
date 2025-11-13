import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
export default function DriverCards({ d }) {
    const priceData = [
        { name: 'A', payable: d.price_value.payable_A },
        { name: 'B', payable: d.price_value.payable_B },
    ];
    const etaData = [
        { name: 'A', eta: d.delivery.eta_A_p50 },
        { name: 'B', eta: d.delivery.eta_B_p50 },
    ];
    const trustData = [
        { name: 'A', rating: d.trust.rating_A, reviews: d.trust.reviews_A },
        { name: 'B', rating: d.trust.rating_B, reviews: d.trust.reviews_B },
    ];
    const fitData = [
        { name: 'A', match: Math.round(d.fit.cuisine_match_A * 100) },
        { name: 'B', match: Math.round(d.fit.cuisine_match_B * 100) },
    ];
    return (_jsxs("div", { className: "grid md:grid-cols-2 gap-4", children: [_jsx(Card, { title: "Price / Value", subtitle: `Coupon usable: A ${d.price_value.coupon_usable_A ? 'yes' : 'no'} • B ${d.price_value.coupon_usable_B ? 'yes' : 'no'}`, children: _jsx(ResponsiveContainer, { width: "100%", height: 180, children: _jsxs(BarChart, { data: priceData, children: [_jsx(CartesianGrid, { stroke: "#2a2f3a", strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "name", stroke: "#9aa3b2" }), _jsx(YAxis, { stroke: "#9aa3b2" }), _jsx(Tooltip, { contentStyle: { background: '#1a1d23', border: '1px solid #2a2f3a' } }), _jsx(Bar, { dataKey: "payable", fill: "var(--brand)", radius: 6 })] }) }) }), _jsx(Card, { title: "Delivery time", subtitle: "ETA p50 (minutes)", children: _jsx(ResponsiveContainer, { width: "100%", height: 180, children: _jsxs(BarChart, { data: etaData, children: [_jsx(CartesianGrid, { stroke: "#2a2f3a", strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "name", stroke: "#9aa3b2" }), _jsx(YAxis, { stroke: "#9aa3b2" }), _jsx(Tooltip, { contentStyle: { background: '#1a1d23', border: '1px solid #2a2f3a' } }), _jsx(Bar, { dataKey: "eta", fill: "var(--brand2)", radius: 6 })] }) }) }), _jsx(Card, { title: "Trust", subtitle: "Rating \u00D7 Reviews", children: _jsx(ResponsiveContainer, { width: "100%", height: 200, children: _jsxs(BarChart, { data: trustData, children: [_jsx(CartesianGrid, { stroke: "#2a2f3a", strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "name", stroke: "#9aa3b2" }), _jsx(YAxis, { yAxisId: "left", stroke: "#9aa3b2" }), _jsx(YAxis, { yAxisId: "right", orientation: "right", stroke: "#9aa3b2" }), _jsx(Tooltip, { contentStyle: { background: '#1a1d23', border: '1px solid #2a2f3a' } }), _jsx(Bar, { yAxisId: "left", dataKey: "rating", fill: "var(--brand)", radius: 6 }), _jsx(Bar, { yAxisId: "right", dataKey: "reviews", fill: "var(--brand2)", radius: 6 })] }) }) }), _jsx(Card, { title: "Preference fit", subtitle: "Cuisine match (%)", children: _jsx(ResponsiveContainer, { width: "100%", height: 180, children: _jsxs(BarChart, { data: fitData, children: [_jsx(CartesianGrid, { stroke: "#2a2f3a", strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "name", stroke: "#9aa3b2" }), _jsx(YAxis, { stroke: "#9aa3b2" }), _jsx(Tooltip, { contentStyle: { background: '#1a1d23', border: '1px solid #2a2f3a' } }), _jsx(Bar, { dataKey: "match", fill: "var(--brand)", radius: 6 })] }) }) })] }));
}
function Card({ title, subtitle, children }) {
    return (_jsxs("div", { className: "card p-4", children: [_jsx("div", { className: "font-semibold", children: title }), subtitle ? _jsx("div", { className: "text-sm text-gray-300 mb-2", children: subtitle }) : null, children] }));
}
