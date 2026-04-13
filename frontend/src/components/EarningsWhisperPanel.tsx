"use client";

interface EarningsWhisperData {
  symbol: string;
  whisper_score: number;
  surprise_probability: number;
  concall_tone: string;
  alternative_data_proxy: string;
  signal: string;
  confidence: number;
  reasoning: string;
  key_triggers: string[];
  is_demo?: boolean;
}

interface EarningsWhisperPanelProps {
  data: EarningsWhisperData | null;
  symbol: string;
}

const TONE_CONFIG: Record<string, { color: string; emoji: string }> = {
  bullish: { color: "text-[var(--color-war-buy)]", emoji: "📈" },
  optimistic: { color: "text-emerald-600", emoji: "✨" },
  cautious: { color: "text-amber-600", emoji: "⚠️" },
  bearish: { color: "text-[var(--color-war-sell)]", emoji: "📉" },
};

export default function EarningsWhisperPanel({ data, symbol }: EarningsWhisperPanelProps) {
  if (!data) {
    return (
      <div className="p-4 border border-[var(--color-war-border)] bg-[#fafaf8]">
        <div className="font-mono text-[10px] uppercase text-[#888] mb-1">🎯 Earnings Whisper</div>
        <p className="font-serif italic text-sm text-[var(--color-war-muted)]">Generating whisper number...</p>
      </div>
    );
  }

  const toneConfig = TONE_CONFIG[data.concall_tone] || { color: "text-gray-600", emoji: "🔍" };
  const beatPct = Math.round(data.surprise_probability * 100);
  const missPct = 100 - beatPct;
  const whisperWidth = `${(data.whisper_score / 10) * 100}%`;

  return (
    <div className="border border-[var(--color-war-border)] bg-[#fafaf8]">
      <div className="flex justify-between items-center px-4 py-2 border-b border-[var(--color-war-border)]">
        <div>
          <span className="font-mono text-[9px] uppercase text-[#888]">🎯 Predictive Earnings Whisper</span>
        <div className="flex gap-2 items-center">
          {data.is_demo && (
            <div className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono text-[8px] font-bold border border-amber-200 animate-pulse">
              SIMULATION
            </div>
          )}
          <p className="font-serif text-sm font-bold">{symbol} Q-Surprise Engine</p>
        </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-lg font-black">{data.whisper_score.toFixed(1)}</div>
          <div className="font-mono text-[8px] uppercase text-[#888]">Whisper Score / 10</div>
        </div>
      </div>

      <div className="p-4">
        {/* Whisper Score Bar */}
        <div className="mb-3">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: whisperWidth,
                backgroundColor:
                  data.whisper_score >= 7 ? "#10b981" : data.whisper_score >= 4 ? "#f59e0b" : "#ef4444",
              }}
            />
          </div>
        </div>

        {/* Beat / Miss Probability */}
        <div className="flex gap-2 mb-3">
          <div className="flex-1 bg-green-50 border border-green-200 p-2 text-center">
            <div className="font-mono text-lg font-black text-[var(--color-war-buy)]">{beatPct}%</div>
            <div className="font-mono text-[8px] uppercase text-[#888]">Beat Prob.</div>
          </div>
          <div className="flex-1 bg-red-50 border border-red-200 p-2 text-center">
            <div className="font-mono text-lg font-black text-[var(--color-war-sell)]">{missPct}%</div>
            <div className="font-mono text-[8px] uppercase text-[#888]">Miss Prob.</div>
          </div>
        </div>

        {/* Concall Tone */}
        <div className="flex items-center gap-2 mb-2 p-2 bg-[#f5f2ec] border border-[var(--color-war-border)]">
          <span className="text-base">{toneConfig.emoji}</span>
          <div>
            <p className="font-mono text-[8px] uppercase text-[#888]">Concall Tone</p>
            <p className={`font-mono text-xs font-bold uppercase ${toneConfig.color}`}>
              {data.concall_tone}
            </p>
          </div>
        </div>

        {/* Alt Data Proxy */}
        <div className="mb-3 p-2 border border-dashed border-[var(--color-war-border)]">
          <p className="font-mono text-[8px] uppercase text-[#888] mb-0.5">Alt-Data Signal</p>
          <p className="font-mono text-[9px] text-[#555]">{data.alternative_data_proxy}</p>
        </div>

        {/* Reasoning */}
        <p className="font-serif italic text-xs leading-relaxed text-[#555] border-l-2 border-[var(--color-war-text)] pl-2">
          {data.reasoning}
        </p>
      </div>
    </div>
  );
}
