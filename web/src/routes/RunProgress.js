import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
export default function RunProgress() {
    const { id } = useParams();
    const nav = useNavigate();
    const location = useLocation();
    const sample = location?.state?.sample ?? 100;
    const [done, setDone] = useState(0);
    const [votes, setVotes] = useState([]);
    useEffect(() => {
        const t = setInterval(() => {
            setDone(d => {
                const nd = Math.min(sample, d + Math.max(1, Math.round(sample / 20)));
                const add = Array.from({ length: nd - d }).map(() => Math.random() < 0.5 ? 'A' : 'B');
                setVotes(v => [...v, ...add]);
                if (nd >= sample) {
                    clearInterval(t);
                    setTimeout(() => nav(`/results/${id}`), 600);
                }
                return nd;
            });
        }, 200);
        return () => clearInterval(t);
    }, [id, nav, sample]);
    const pct = Math.round((done / sample) * 100);
    return (_jsxs("main", { className: "max-w-3xl mx-auto p-6 space-y-6", children: [_jsx("h1", { className: "text-3xl font-bold", children: "Running" }), _jsxs("p", { className: "text-gray-300", children: ["Evaluating ", sample, " twins\u2026"] }), _jsx("div", { className: "w-full h-3 bg-[#1f232b] rounded-xl overflow-hidden", children: _jsx("div", { className: "h-full bg-[var(--brand2)]", style: { width: `${pct}%` } }) }), _jsx("div", { className: "grid grid-cols-10 gap-2", children: votes.slice(-50).map((v, i) => (_jsx("div", { className: `h-6 rounded-full ${v === 'A' ? 'bg-[var(--brand)]' : 'bg-[var(--brand2)]'}` }, i))) }), _jsx("button", { className: "btn btn-secondary", onClick: () => nav(`/results/${id}`), children: "Go to results when ready" })] }));
}
