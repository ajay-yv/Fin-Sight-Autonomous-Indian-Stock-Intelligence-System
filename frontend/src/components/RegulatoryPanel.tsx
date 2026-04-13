"use client";

interface RegEvent {
  category: string;
  risk_score: number;
  description: string;
}

interface RegulatoryData {
  symbol: string;
  events: RegEvent[];
  max_risk_score: number;
  sentiment_impact: string;
  signal: string;
  confidence: number;
  reasoning: string;
  key_triggers: string[];
  is_demo: boolean;
}

interface RegulatoryPanelProps {
  data: RegulatoryData | null;
  symbol: string;
}

export default function RegulatoryPanel({ data, symbol }: RegulatoryPanelProps) {
  if (!data) {
    return (
      <div className="p-4 border border-[var(--color-war-border)] bg-[#fafaf8]">
        <div className="font-mono text-[10px] uppercase text-[#888] mb-1">🏛️ SEBI Regulatory Radar</div>
        <p className="font-serif italic text-sm text-[var(--color-war-muted)]">Scanning SEBI filings...</p>
      </div>
    );
  }

  const riskColor =
    data.max_risk_score >= 7
      ? "text-[var(--color-war-sell)]"
      : data.max_risk_score >= 4
      ? "text-amber-600"
      : "text-[var(--color-war-buy)]";

  const riskBg =
    data.max_risk_score >= 7
      ? "bg-red-50 border-red-300"
      : data.max_risk_score >= 4
      ? "bg-amber-50 border-amber-300"
      : "bg-green-50 border-green-300";

  return (
    <div className="border border-[var(--color-war-border)] bg-[#fafaf8]">
      <div className="flex justify-between items-center px-4 py-2 border-b border-[var(--color-war-border)]">
        <div>
          <span className="font-mono text-[9px] uppercase text-[#888]">🏛️ SEBI Regulatory Radar</span>
          <p className="font-serif text-sm font-bold">{symbol} Compliance Status</p>
        </div>
        <div className="flex gap-2 items-center">
          {data.is_demo && (
            <div className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono text-[8px] font-bold border border-amber-200 animate-pulse">
              SIMULATION
            </div>
          )}
          <div className={`border px-2 py-0.5 font-mono text-[10px] font-bold ${riskBg} ${riskColor}`}>
            RISK: {data.max_risk_score.toFixed(1)}/10
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Risk Bar */}
        <div className="mb-3">
          <div className="flex justify-between mb-1">
            <span className="font-mono text-[9px] uppercase text-[#888]">Regulatory Risk Score</span>
            <span className={`font-mono text-xs font-bold ${riskColor}`}>
              {data.sentiment_impact.toUpperCase()} IMPACT
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${data.max_risk_score * 10}%`,
                backgroundColor:
                  data.max_risk_score >= 7 ? "#ef4444" : data.max_risk_score >= 4 ? "#f59e0b" : "#10b981",
              }}
            />
          </div>
        </div>

        {/* Events */}
        {data.events.length > 0 ? (
          <div className="space-y-2 mb-3">
            <p className="font-mono text-[8px] uppercase text-[#888]">Categorized Events ({data.events.length})</p>
            {data.events.slice(0, 3).map((evt, i) => (
              <div key={i} className="flex items-start gap-2 border-l-2 border-amber-400 pl-2">
                <div>
                  <span className="font-mono text-[9px] font-bold uppercase">{evt.category}</span>
                  <p className="font-mono text-[8px] text-[#666]">{evt.description}</p>
                </div>
                <span className={`font-mono text-[9px] font-bold ml-auto shrink-0 ${evt.risk_score >= 7 ? "text-red-600" : "text-amber-600"}`}>
                  {evt.risk_score.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="mb-3 p-2 bg-green-50 border border-green-200 font-mono text-[9px] text-green-700">
            ✓ No significant regulatory events detected.
          </div>
        )}

        <p className="font-serif italic text-xs leading-relaxed text-[#555] border-l-2 border-[var(--color-war-text)] pl-2">
          {data.reasoning}
        </p>
      </div>
    </div>
  );
}
