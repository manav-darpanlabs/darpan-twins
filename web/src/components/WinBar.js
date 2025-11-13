import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export default function WinBar({ A, B, tie }) {
    const a = Math.round(A * 100);
    const b = Math.round(B * 100);
    const t = Math.round(tie * 100);
    const total = a + b + t || 1;
    return (_jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "w-full h-5 bg-[#1f232b] rounded-xl overflow-hidden flex", children: [_jsx("div", { style: { width: `${(a / total) * 100}%`, background: 'var(--brand)' } }), _jsx("div", { style: { width: `${(b / total) * 100}%`, background: 'var(--brand2)' } }), _jsx("div", { style: { width: `${(t / total) * 100}%`, background: '#2f3542' } })] }), _jsxs("div", { className: "flex gap-4 text-sm text-gray-300", children: [_jsxs("span", { children: ["A: ", a, "%"] }), _jsxs("span", { children: ["B: ", b, "%"] }), _jsxs("span", { children: ["Tie: ", t, "%"] })] })] }));
}
