export function copyMarkdownSummary(d) {
    const a = Math.round(d.aggregate.A * 100);
    const b = Math.round(d.aggregate.B * 100);
    const t = Math.round(d.aggregate.tie * 100);
    const top = d.top_reasons
        .slice(0, 3)
        .map((r) => `- ${r.driver}: ${r.summary}`)
        .join('\n');
    const rec = d.recommended_actions
        .slice(0, 3)
        .map((x) => `- ${x}`)
        .join('\n');
    return `# Experiment ${d.experiment_id} — ${d.city}\n\nA: ${a}%  B: ${b}%  Tie: ${t}%\n\n## Top reasons\n${top}\n\n## Recommended actions\n${rec}\n\nLink: about:blank?exp=${encodeURIComponent(d.experiment_id)}\n`;
}
