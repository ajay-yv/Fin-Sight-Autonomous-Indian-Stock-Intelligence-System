"use client";

interface SocialPulseData {
  symbol: string;
  social_score: number;
  volume_spike_flag: boolean;
  dominant_platform: string;
  top_keywords: string[];
  sentiment_label: string;
  signal: string;
  confidence: number;
  reasoning: string;
  key_triggers: string[];
  is_demo?: boolean;
}

interface SocialPulsePanelProps {
  data: SocialPulseData | null;
  symbol: string;
}

export default function SocialPulsePanel({ data, symbol }: SocialPulsePanelProps) {
  if (!data) {
    return (
      <div className="p-4 border border-[var(--color-war-border)] bg-[#fafaf8]">
        <div className="font-mono text-[10px] uppercase text-[#888] mb-1">🧠 Dalal Street Pulse</div>
        <p className="font-serif italic text-sm text-[var(--color-war-muted)]">Awaiting social intelligence...</p>
      </div>
    );
  }

  const scoreWidth = `${((data.social_score + 1) / 2) * 100}%`;
  const sentimentColor =
    data.sentiment_label === "positive"
      ? "text-[var(--color-war-buy)]"
      : data.sentiment_label === "negative"
      ? "text-[var(--color-war-sell)]"
      : "text-amber-600";

  return (
    <div className="border border-[var(--color-war-border)] bg-[#fafaf8]">
      <div className="flex justify-between items-center px-4 py-2 border-b border-[var(--color-war-border)]">
        <div>
          <span className="font-mono text-[9px] uppercase text-[#888]">🧠 Dalal Street Social Pulse</span>
          <p className="font-serif text-sm font-bold">{symbol} Social Intelligence</p>
        </div>
        <div className="flex gap-2">
          {data.is_demo && (
            <div className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono text-[8px] font-bold border border-amber-200 animate-pulse">
              SIMULATION
            </div>
          )}
          {data.volume_spike_flag && (
            <span className="bg-red-100 text-red-700 font-mono text-[8px] px-2 py-0.5 border border-red-400 animate-pulse">
              SPIKE
            </span>
          )}
        </div>
      </div>

      <div className="p-4">
        {/* Sentiment Bar */}
        <div className="mb-3">
          <div className="flex justify-between mb-1">
            <span className="font-mono text-[9px] uppercase text-[#888]">Social Score</span>
            <span className={`font-mono text-xs font-bold ${sentimentColor}`}>
              {data.social_score > 0 ? "+" : ""}{data.social_score.toFixed(2)} ({data.sentiment_label})
            </span>
          </div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden relative">
            <div className="absolute left-1/2 h-full w-px bg-gray-400" />
            <div
              className="h-full rounded-full absolute"
              style={{
                left: data.social_score < 0 ? scoreWidth : "50%",
                width: `${Math.abs(data.social_score) * 50}%`,
                backgroundColor: data.social_score > 0 ? "#10b981" : "#ef4444",
              }}
            />
          </div>
          <div className="flex justify-between mt-0.5">
            <span className="font-mono text-[8px] text-[#888]">Bearish</span>
            <span className="font-mono text-[8px] text-[#888]">Bullish</span>
          </div>
        </div>

        {/* Platform & Keywords */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <p className="font-mono text-[8px] uppercase text-[#888] mb-1">Dominant Platform</p>
            <p className="font-mono text-xs font-bold">{data.dominant_platform}</p>
          </div>
          <div>
            <p className="font-mono text-[8px] uppercase text-[#888] mb-1">Confidence</p>
            <p className="font-mono text-xs font-bold">{(data.confidence * 100).toFixed(0)}%</p>
          </div>
        </div>

        {/* Keywords */}
        {data.top_keywords.length > 0 && (
          <div className="mb-3">
            <p className="font-mono text-[8px] uppercase text-[#888] mb-1">Top Keywords</p>
            <div className="flex flex-wrap gap-1">
              {data.top_keywords.map((kw, i) => (
                <span key={i} className="font-mono text-[9px] bg-gray-100 border border-gray-300 px-1.5 py-0.5">
                  #{kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Reasoning */}
        <p className="font-serif italic text-xs leading-relaxed text-[#555] border-l-2 border-[var(--color-war-text)] pl-2">
          {data.reasoning}
        </p>
      </div>
    </div>
  );
}
