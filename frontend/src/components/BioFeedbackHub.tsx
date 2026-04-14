"use client";

import { useState, useEffect } from "react";
import { LucideHeartPulse, LucideShieldAlert, LucideBrain, LucideZap, LucideMessageCircle, LucideActivity } from "lucide-react";

interface Biometric {
  hrv: number;
  bpm: number;
  respiratory_rate: number;
  cortisol_index: number;
  sleep_quality_score: number;
}

interface Sanity {
  fatigue_level: number;
  emotional_state: string;
  risk_multiplier: number;
  is_guardrail_active: boolean;
  reasoning: string;
}

interface Guidance {
  reflective_question: string;
  suggested_action: string;
  mistral_analysis: string;
}

export default function BioFeedbackHub({ onBack }: { onBack?: () => void }) {
  const [data, setData] = useState<{ vitals: Biometric; sanity: Sanity; guidance: Guidance } | null>(null);
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

  useEffect(() => {
    fetchBioSync();
    const interval = setInterval(fetchBioSync, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchBioSync = async () => {
    try {
      const res = await fetch(`/api/biofeedback/status`);
      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error("Bio-Feedback sync failed", err);
    }
  };

  if (!data || !data.vitals || !data.sanity) {
    return (
      <div className="p-8 flex flex-col h-full bg-[#0a0a0a]">
        {onBack && (
            <button onClick={onBack} className="self-start text-[10px] uppercase font-bold text-zinc-500 hover:text-white mb-4 transition-colors">← Return to Dashboard</button>
        )}
        <div className="p-8 font-mono text-xs text-rose-400 bg-rose-950/20 border border-rose-900/50 rounded-lg">
            <p className="font-bold mb-2 flex items-center gap-2">
            <LucideShieldAlert size={14} />
            ⚠ BIOMETRIC SYNC DISTURBANCE
            </p>
            <p className="opacity-70 mb-4">Waiting for valid biometric stream from agents... (Check backend liveness)</p>
            <div className="animate-pulse flex space-x-2">
                <div className="h-1 w-1 bg-rose-500 rounded-full"></div>
                <div className="h-1 w-1 bg-rose-500 rounded-full animate-delay-100"></div>
                <div className="h-1 w-1 bg-rose-500 rounded-full animate-delay-200"></div>
            </div>
        </div>
      </div>
    );
  }

  const { vitals, sanity, guidance } = data;

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a] text-white font-mono overflow-y-auto">
      {/* Bio Header */}
      <div className="p-6 border-b border-[#222] flex justify-between items-center bg-[#111] sticky top-0 z-10">
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
            <h2 className="text-xl font-bold tracking-tighter flex items-center gap-2 text-rose-500">
              <LucideHeartPulse size={20} className="animate-pulse" />
              FINANCIAL HEALTH HUB
            </h2>
            <p className="text-[9px] uppercase tracking-widest text-[#555]">Biometric Guardrail v5.0-Mistral</p>
          </div>
        </div>
        <div className={`px-4 py-1 rounded-full border text-[10px] font-bold ${sanity?.is_guardrail_active ? "border-rose-500 text-rose-500 bg-rose-500/10" : "border-emerald-500 text-emerald-500 bg-emerald-500/10"}`}>
          {sanity?.is_guardrail_active ? "GUARDRAILS ACTIVE" : "OPTIMAL PERFORMANCE"}
        </div>
      </div>

      <div className="p-8 space-y-8 max-w-6xl mx-auto w-full flex-1">
        {/* Vitals Grid */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-[#151515] p-4 rounded border border-[#222]">
            <div className="text-[9px] text-[#555] uppercase mb-1">Market Vol Index</div>
            <div className="text-2xl font-black">{vitals?.bpm?.toFixed(1) || "0.0"} <span className="text-[10px] font-normal text-[#444]">VIX</span></div>
          </div>
          <div className="bg-[#151515] p-4 rounded border border-[#222]">
            <div className="text-[9px] text-[#555] uppercase mb-1">Vol Momentum (1h)</div>
            <div className="text-2xl font-black text-rose-400">{vitals?.hrv?.toFixed(1) || "0.0"} <span className="text-[10px] font-normal text-[#444]">Δ</span></div>
          </div>
          <div className="bg-[#151515] p-4 rounded border border-[#222]">
            <div className="text-[9px] text-[#555] uppercase mb-1">Trade Density</div>
            <div className="text-2xl font-black text-amber-500">{((vitals?.cortisol_index || 0) * 100).toFixed(0)} <span className="text-[10px] font-normal text-[#444]">%</span></div>
          </div>
          <div className="bg-[#151515] p-4 rounded border border-[#222]">
            <div className="text-[9px] text-[#555] uppercase mb-1">Market Sentiment</div>
            <div className="text-2xl font-black text-emerald-400">{((vitals?.sleep_quality_score || 0) * 100).toFixed(0)} <span className="text-[10px] font-normal text-[#444]">%</span></div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-8">
          {/* Risk Overrides */}
          <div className="col-span-2 space-y-6">
            <div className={`p-6 rounded-lg border-2 ${sanity?.is_guardrail_active ? "bg-rose-500/5 border-rose-500/30" : "bg-emerald-500/5 border-emerald-500/30"}`}>
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${sanity?.is_guardrail_active ? "bg-rose-500 text-white" : "bg-emerald-500 text-white"}`}>
                  {sanity?.is_guardrail_active ? <LucideShieldAlert size={24} /> : <LucideZap size={24} />}
                </div>
                <div>
                  <h3 className="text-lg font-bold uppercase italic">{sanity?.emotional_state || "UNKNOWN"} MARKET STATE</h3>
                  <p className="text-xs text-[#888] mt-2 mb-4 leading-relaxed">{sanity?.reasoning || "Analyzing market vitals..."}</p>
                  
                  <div className="flex gap-4">
                    <div className="bg-black/40 px-4 py-2 rounded text-[10px]">
                      <span className="text-[#555] block uppercase">Panic Multiplier</span>
                      <span className="font-bold text-lg text-rose-400">x{sanity?.risk_multiplier?.toFixed(2) || "1.00"}</span>
                    </div>
                    <div className="bg-black/40 px-4 py-2 rounded text-[10px]">
                      <span className="text-[#555] block uppercase">Volatility Stress</span>
                      <span className="font-bold text-lg">{((sanity?.fatigue_level || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Waveform Mock */}
            <div className="bg-[#111] border border-[#222] p-6 rounded-lg">
                <h4 className="text-[10px] font-bold text-[#444] uppercase mb-4 flex items-center gap-2">
                    <LucideActivity size={14} className="text-rose-500" />
                    Market 'Heartbeat' (Volatility Frequency)
                </h4>
                <div className="h-24 w-full flex items-end gap-1 px-4 overflow-hidden mask-fade-edges">
                    {Array.from({ length: 40 }).map((_, i) => (
                        <div 
                            key={i} 
                            className="bg-rose-500/20 w-full" 
                            style={{ 
                                height: `${Math.floor(Math.random() * (sanity?.is_guardrail_active ? 40 : 80)) + 10}%`,
                                transition: 'height 0.3s ease' 
                            }} 
                        />
                    ))}
                </div>
            </div>
          </div>

          {/* Behavioral Coach */}
          <div className="bg-[#151515] border border-[#222] p-6 rounded-lg flex flex-col h-full">
            <h4 className="text-[10px] font-bold text-[#444] uppercase mb-6 flex items-center gap-2">
                <LucideBrain size={16} className="text-purple-500" />
                Mistral Behavioral Coach
            </h4>
            
            <div className="flex-1 space-y-6">
                <div className="bg-purple-500/5 border border-purple-500/20 p-4 rounded text-xs italic text-zinc-300 leading-relaxed">
                    "{guidance?.reflective_question || "Maintaining discipline in all market conditions."}"
                </div>

                <div className="space-y-4">
                    <div className="text-[9px] uppercase text-[#444] font-bold">Recommended Protocol</div>
                    <div className="bg-zinc-900 border border-[#333] px-4 py-3 text-[10px] font-bold text-purple-400">
                        &gt; {guidance?.suggested_action?.replace(/_/g, " ") || "STAY_DISCIPLINED"}
                    </div>
                </div>

                <div className="text-[9px] text-zinc-500 leading-normal">
                    <LucideMessageCircle size={10} className="inline mr-1 mb-0.5" />
                    {guidance?.mistral_analysis || "Stable baseline observed. No immediate risk intervention required."}
                </div>
            </div>

            <button className="mt-8 w-full py-4 bg-zinc-900 hover:bg-zinc-800 border border-[#333] text-[10px] uppercase font-bold tracking-[0.2em] transition-all">
                Acknowledge & Sync
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
