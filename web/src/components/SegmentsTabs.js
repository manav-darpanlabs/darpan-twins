import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export default function SegmentsTabs({ segments }) {
    if (!segments?.length)
        return null;
    const s = segments[0];
    return (_jsxs("div", { className: "space-y-2", children: [_jsx("div", { className: "flex gap-2 flex-wrap", children: _jsx("span", { className: "chip", children: s.name }) }), _jsx("div", { className: "grid md:grid-cols-3 gap-3", children: s.buckets.map((b) => (_jsxs("div", { className: "card p-3", children: [_jsx("div", { className: "text-sm text-gray-300 mb-1", children: b.label }), _jsx(Stacked, { label: "A", a: b.A, b: b.B, t: b.tie })] }, b.label))) })] }));
}
function Stacked({ label, a, b, t }) {
    const A = Math.round(a * 100);
    const B = Math.round(b * 100);
    const T = Math.round(t * 100);
    const total = A + B + T || 1;
    return (_jsxs("div", { children: [_jsxs("div", { className: "w-full h-3 bg-[#1f232b] rounded-xl overflow-hidden flex", children: [_jsx("div", { style: { width: `${(A / total) * 100}%`, background: 'var(--brand)' } }), _jsx("div", { style: { width: `${(B / total) * 100}%`, background: 'var(--brand2)' } }), _jsx("div", { style: { width: `${(T / total) * 100}%`, background: '#2f3542' } })] }), _jsxs("div", { className: "text-xs text-gray-400 mt-1", children: ["A ", A, "% \u2022 B ", B, "% \u2022 Tie ", T, "%"] })] }));
}
