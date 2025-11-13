import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useNavigate } from 'react-router-dom';
import { useMemo, useState } from 'react';
export default function ExperimentForm() {
    const nav = useNavigate();
    const [city, setCity] = useState('');
    const [cardA, setCardA] = useState(null);
    const [cardB, setCardB] = useState(null);
    const [name, setName] = useState('City AB Test');
    const [sample, setSample] = useState(100);
    const ready = useMemo(() => city && cardA && cardB, [city, cardA, cardB]);
    function start() {
        const id = `EXP-${new Date().toISOString().slice(0, 10)}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
        nav(`/run/${id}`, { state: { name, city, sample } });
    }
    return (_jsxs("main", { className: "max-w-6xl mx-auto p-6 space-y-6", children: [_jsxs("section", { className: "space-y-1", children: [_jsx("h1", { className: "text-3xl font-bold", children: "Create an experiment" }), _jsx("p", { className: "text-gray-300 max-w-2xl", children: "Select the city, upload two restaurant cards, and specify context. We\u2019ll ask your customer twins to choose A or B and explain why." })] }), _jsxs("div", { className: "grid md:grid-cols-2 gap-6", children: [_jsxs("div", { className: "card p-4 space-y-3", children: [_jsx("label", { className: "text-sm text-gray-300", children: "Experiment name" }), _jsx("input", { className: "w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2", value: name, onChange: e => setName(e.target.value) }), _jsx("label", { className: "text-sm text-gray-300", children: "City" }), _jsx("input", { placeholder: "Mumbai", className: "w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2", value: city, onChange: e => setCity(e.target.value) }), _jsx("label", { className: "text-sm text-gray-300", children: "Twin sample size" }), _jsx("input", { type: "number", min: 10, max: 1000, className: "w-full bg-[#0f1218] border border-[#232838] rounded-xl px-3 py-2", value: sample, onChange: e => setSample(parseInt(e.target.value || '0')) })] }), _jsxs("div", { className: "card p-4 space-y-3", children: [_jsxs("div", { children: [_jsx("label", { className: "text-sm text-gray-300", children: "Card A (PNG/JPG)" }), _jsx("input", { type: "file", accept: "image/*", onChange: e => setCardA(e.target.files?.[0] || null) })] }), _jsxs("div", { children: [_jsx("label", { className: "text-sm text-gray-300", children: "Card B (PNG/JPG)" }), _jsx("input", { type: "file", accept: "image/*", onChange: e => setCardB(e.target.files?.[0] || null) })] })] })] }), _jsx("div", { className: "flex justify-end", children: _jsx("button", { className: `btn ${ready ? 'btn-primary' : 'opacity-50 cursor-not-allowed btn-primary'}`, onClick: start, disabled: !ready, children: "Start experiment" }) })] }));
}
