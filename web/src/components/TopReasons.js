import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export default function TopReasons({ reasons }) {
    return (_jsx("ul", { className: "list-disc pl-5 space-y-2", children: reasons.map((r, i) => (_jsxs("li", { children: [_jsx("span", { className: "chip mr-2", children: r.driver }), r.summary, _jsx("span", { className: "ml-2 text-xs text-gray-400", children: r.evidence.map((e) => (_jsx("span", { className: "chip mr-1", children: e }, e))) })] }, i))) }));
}
