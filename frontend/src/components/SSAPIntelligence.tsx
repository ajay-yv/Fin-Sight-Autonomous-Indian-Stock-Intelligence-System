"use client";

import { useState, useEffect } from "react";
import { LucideSatellite, LucideMessageSquare, LucideAlertTriangle, LucideTrendingUp, LucideScan } from "lucide-react";

interface SatelliteInsight {
  area_id: string;
  timestamp: string;
  activity_type: string;
  density_score: number;
  object_counts: Record<string, number>;
  image_url?: string;
  confidence: number;
}

interface SentimentInsight {
  protocol: string;
  symbol: string;
  timestamp: string;
  mention_volume: number;
  sentiment_score: number;
  top_keywords: string[];
  trending_score: number;
  raw_sample_posts: string[];
}

interface SSAPVerdict {
  symbol: string;
  run_id: string;
  timestamp: string;
  geospatial_summary: string;
  sentiment_summary: string;
  alpha_discrepancy: boolean;
  discrepancy_score: number;
  prediction: "BULLISH_SURPRISE" | "BEARISH_SURPRISE" | "NEUTRAL";
  reasoning: string;
  confidence_score: number;
}

export default function SSAPIntelligence({ symbol, onBack }: { symbol: string, onBack?: () => void }) {
  const [verdict, setVerdict] = useState<SSAPVerdict | null>(null);
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

  useEffect(() => {
    if (symbol) fetchVerdict();
  }, [symbol]);

  const fetchVerdict = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/ssap/verdict/${symbol}`);
      const data = await res.json();
      setVerdict(data);
    } catch (err) {
      console.error("SSAP Analysis failed", err);
    } finally {
      setLoading(false);
    }
  };

  if (!symbol) return (
    <div className="p-8 flex flex-col h-full bg-[#0a0a0a]">
        {onBack && (
            <button onClick={onBack} className="self-start text-[10px] uppercase font-bold text-zinc-500 hover:text-white mb-4">← Return to Dashboard</button>
        )}
        <div className="font-mono text-xs opacity-50 italic">Select an asset to initialize SSAP...</div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a] text-white font-mono overflow-y-auto">
      {/* Header */}
      <div className="p-6 border-b border-[#333] flex justify-between items-center bg-[#111] sticky top-0 z-10">
        <div className="flex items-center gap-6">
          {onBack && (
            <button 
              onClick={onBack}
              className="px-3 py-2 border border-[#333] rounded hover:border-[#666] hover:bg-[#222] transition-all group"
            >
              <span className="text-[10px] uppercase font-bold text-zinc-500 group-hover:text-white transition-colors">← DASHBOARD</span>
            </button>
          )}
          <div>
            <h2 className="text-xl font-bold tracking-tighter flex items-center gap-2 text-cyan-400">
              <LucideSatellite size={20} />
              SSAP MULTIMODAL ALPHA
            </h2>
            <p className="text-[9px] uppercase tracking-widest text-[#666]">Satellite-to-Sentiment Alpha Predictor v1.0</p>
          </div>
        </div>
        {verdict && (
          <div className="text-right">
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${verdict.alpha_discrepancy ? "bg-amber-500 text-black" : "bg-zinc-800 text-zinc-400"}`}>
              {verdict.alpha_discrepancy ? "DISCREPANCY DETECTED" : "SIGNALS ALIGNED"}
            </span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 opacity-50">
          <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-[10px] uppercase tracking-[0.2em]">Tasking SkyWatch & Crawling DeSo...</span>
        </div>
      ) : verdict ? (
        <div className="p-6 space-y-8 max-w-5xl mx-auto w-full">
          {/* Main Verdict Card */}
          <div className={`p-6 border-l-4 ${verdict.prediction === "BULLISH_SURPRISE" ? "border-green-500 bg-green-500/5" : verdict.prediction === "BEARISH_SURPRISE" ? "border-red-500 bg-red-500/5" : "border-zinc-500 bg-zinc-500/5"}`}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-2xl font-black italic">{verdict.prediction.replace("_", " ")}</h3>
                <p className="text-xs text-[#aaa] mt-1">{verdict.reasoning}</p>
              </div>
              <LucideAlertTriangle size={32} className={verdict.alpha_discrepancy ? "text-amber-500" : "text-zinc-700"} />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="bg-[#1a1a1a] p-3 rounded border border-[#333]">
                <div className="text-[9px] text-[#666] uppercase mb-1">Discrepancy Intensity</div>
                <div className="flex items-end gap-2">
                  <span className="text-xl font-bold">{(verdict.discrepancy_score * 100).toFixed(1)}%</span>
                  <div className="flex-1 h-1 bg-zinc-800 rounded-full mb-1.5 overflow-hidden">
                    <div className="h-full bg-cyan-500 transition-all duration-1000" style={{ width: `${verdict.discrepancy_score * 100}%` }} />
                  </div>
                </div>
              </div>
              <div className="bg-[#1a1a1a] p-3 rounded border border-[#333]">
                <div className="text-[9px] text-[#666] uppercase mb-1">Confidence Score</div>
                <div className="flex items-end gap-2">
                  <span className="text-xl font-bold">{(verdict.confidence_score * 100).toFixed(1)}%</span>
                  <div className="flex-1 h-1 bg-zinc-800 rounded-full mb-1.5 overflow-hidden">
                    <div className="h-full bg-purple-500" style={{ width: `${verdict.confidence_score * 100}%` }} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Geospatial Panel */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-cyan-500/30 pb-2">
                <LucideScan size={14} className="text-cyan-500" />
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-cyan-500">Physical Activity (Optical/SAR)</h4>
              </div>
              
              <div className="aspect-video bg-[#1a1a1a] rounded border border-[#333] relative overflow-hidden group">
                <img 
                  src={verdict.geospatial_summary.includes("Standard") 
                    ? "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=1000"
                    : "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1000"
                  } 
                  alt="Satellite Detection"
                  className="w-full h-full object-cover opacity-80 group-hover:scale-110 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent p-4 flex flex-col justify-end">
                  <span className="text-[10px] font-bold bg-cyan-500 text-black px-1.5 py-0.5 w-fit rounded mb-2">OPERATIONAL SIGNAL: {verdict.alpha_discrepancy ? "ANOMALY" : "ACTIVE"}</span>
                  <div className="flex gap-4 text-[10px]">
                    <span>INTENSITY: {(verdict.discrepancy_score * 100).toFixed(1)}%</span>
                    <span>CONFIDENCE: {(verdict.confidence_score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-[#888] italic">"{verdict.geospatial_summary}"</p>
            </div>

            {/* Sentiment Panel */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-purple-500/30 pb-2">
                <LucideMessageSquare size={14} className="text-purple-500" />
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-purple-500">News Sentiment (Multi-Source)</h4>
              </div>
              
              <div className="bg-[#1a1a1a] rounded border border-[#333] p-4 min-h-[160px] flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-[#666]">News Cycles Analyzed</span>
                    <span className="font-bold">Real-Time (YF)</span>
                  </div>
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 transition-all duration-1000" style={{ width: `${Math.abs(verdict.discrepancy_score * 100)}%` }} />
                  </div>
                </div>

                <div className="mt-4 bg-[#222] p-3 border-l-2 border-purple-500 italic text-[10px] text-zinc-400">
                  {verdict.sentiment_summary}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {["#realtime", "#news", "#sentiment", "#alpha"].map(tag => (
                    <span key={tag} className="text-[8px] border border-[#333] px-1.5 py-0.5 rounded text-zinc-500">{tag}</span>
                  ))}
                </div>
              </div>
              <p className="text-[10px] text-[#888] italic">"Fusing global headlines with operational footprints to derive alpha."</p>
            </div>
          </div>

          <button 
            onClick={fetchVerdict}
            className="w-full py-4 bg-zinc-900 border border-[#333] hover:border-cyan-500 hover:text-cyan-500 transition-all font-bold uppercase tracking-widest text-[11px] flex items-center justify-center gap-2"
          >
            <LucideTrendingUp size={14} />
            Refresh Multimodal Sweep
          </button>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center opacity-30 italic text-sm">
          Awaiting initialization sequence...
        </div>
      )}
    </div>
  );
}
