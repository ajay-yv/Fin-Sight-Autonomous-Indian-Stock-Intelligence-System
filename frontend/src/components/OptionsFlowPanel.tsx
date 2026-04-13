"use client";

interface OptionsFlowData {
  symbol: string;
  pcr: number;
  iv_rank: number;
  max_pain: number;
  gex_net: number;
  oi_change_velocity: number;
  signal: string;
  confidence: number;
  reasoning: string;
  key_triggers: string[];
  is_demo?: boolean;
}

interface OptionsFlowPanelProps {
  data: OptionsFlowData | null;
  symbol: string;
}

function MetricBar({ value, min, max, label, format }: {
  value: number;
  min: number;
  max: number;
  label: string;
  format: (v: number) => string;
}) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const isNeg = value < 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <span className="font-mono text-[9px] uppercase text-[#888]">{label}</span>
        <span className={`font-mono text-xs font-bold ${isNeg ? "text-red-600" : "text-[var(--color-war-text)]"}`}>
          {format(value)}
        </span>
      </div>
      <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: pct > 70 ? "#10b981" : pct > 35 ? "#f59e0b" : "#ef4444" }}
        />
      </div>
    </div>
  );
}

export default function OptionsFlowPanel({ data, symbol }: OptionsFlowPanelProps) {
  if (!data) {
    return (
      <div className="p-4 border border-[var(--color-war-border)] bg-[#fafaf8]">
        <div className="font-mono text-[10px] uppercase text-[#888] mb-1">F&O Dark Pool Radar</div>
        <p className="font-serif italic text-sm text-[var(--color-war-muted)]">
          Awaiting options flow data...
        </p>
      </div>
    );
  }

  const signalColor =
    data.signal === "BUY"
      ? "text-[var(--color-war-buy)] border-[var(--color-war-buy)]"
      : data.signal === "SELL"
      ? "text-[var(--color-war-sell)] border-[var(--color-war-sell)]"
      : "text-amber-600 border-amber-600";

  return (
    <div className="border border-[var(--color-war-border)] bg-[#fafaf8]">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-2 border-b border-[var(--color-war-border)]">
        <div>
          <span className="font-mono text-[9px] uppercase text-[#888]">
            🐋 F&O Dark Pool Radar
          </span>
          <p className="font-serif text-sm font-bold">{symbol} Options Flow</p>
        </div>
        <div className="flex gap-2 items-center">
          {data.is_demo && (
            <div className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono text-[8px] font-bold border border-amber-200 animate-pulse">
              SIMULATION
            </div>
          )}
          <div className={`border px-2 py-0.5 font-mono text-[10px] font-bold ${signalColor}`}>
            {data.signal}
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Metrics */}
        <MetricBar
          value={data.pcr}
          min={0}
          max={2}
          label="Put-Call Ratio (PCR)"
          format={(v) => v.toFixed(2)}
        />
        <MetricBar
          value={data.iv_rank}
          min={0}
          max={100}
          label="IV Rank (%)"
          format={(v) => `${v.toFixed(1)}%`}
        />
        <MetricBar
          value={data.gex_net + 5}
          min={0}
          max={10}
          label="Gamma Exposure (GEX)"
          format={(v) => `${(v - 5).toFixed(2)} Bn`}
        />
        <MetricBar
          value={data.oi_change_velocity}
          min={0}
          max={2}
          label="OI Change Velocity"
          format={(v) => `${v.toFixed(2)}x`}
        />

        {/* Max Pain */}
        <div className="flex justify-between items-center mb-3 pt-1 border-t border-[var(--color-war-border)]">
          <span className="font-mono text-[9px] uppercase text-[#888]">Max Pain Strike</span>
          <span className="font-mono text-sm font-bold">₹{data.max_pain.toLocaleString()}</span>
        </div>

        {/* Reasoning */}
        <p className="font-serif italic text-xs leading-relaxed text-[#555] border-l-2 border-[var(--color-war-text)] pl-2 mb-2">
          {data.reasoning}
        </p>

        {/* Triggers */}
        {data.key_triggers.length > 0 && (
          <div className="space-y-1">
            {data.key_triggers.map((t, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="text-[var(--color-war-text)] font-bold text-[10px]">→</span>
                <span className="font-mono text-[9px] text-[#666]">{t}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
