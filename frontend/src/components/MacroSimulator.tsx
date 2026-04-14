"use client";

import { useState, useEffect } from "react";
import { LucideGlobe, LucideAlertCircle, LucideLayers, LucideLineChart, LucideActivity, LucideShare2, LucidePlay } from "lucide-react";

interface MacroShock {
  shock_id: string;
  event_type: string;
  description: string;
  initial_magnitude: number;
  target_sectors: string[];
  duration_months: number;
}

interface PropagationDelta {
  step: number;
  target_sector: string;
  inflation_delta: number;
  supply_chain_stress: number;
  gdp_impact: number;
  market_volatility: number;
}

interface SimulationReport {
  simulation_id: string;
  shock: MacroShock;
  propagation_steps: PropagationDelta[];
  affected_sectors: string[];
  max_supply_chain_stress: number;
  recovery_estimated_months: number;
  narrative_summary: string;
}

export default function MacroSimulator({ onBack }: { onBack?: () => void }) {
  const [report, setReport] = useState<SimulationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeScenario, setActiveScenario] = useState("SUEZ_BLOCKAGE");
  const [macroBaselines, setMacroBaselines] = useState<any>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

  useEffect(() => {
    fetchMacroBaselines();
  }, []);

  const fetchMacroBaselines = async () => {
    try {
      const res = await fetch(`/api/stock/macro-indicators`);
      const data = await res.json();
      setMacroBaselines(data);
    } catch (err) {
      console.error("Failed to fetch macro baselines", err);
    }
  };

  const runSimulation = async (key: string) => {
    setLoading(true);
    setActiveScenario(key);
    try {
      const res = await fetch(`/api/gmss/simulate/${key}`, { method: "POST" });
      const data = await res.json();
      setReport(data);
    } catch (err) {
      console.error("Simulation failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full bg-[#080808] text-[#eee] font-mono overflow-hidden">
      {/* Sidebar: Scenarios */}
      <div className="w-80 border-r border-[#1a1a1a] bg-[#0c0c0c] flex flex-col">
        <div className="p-6 border-b border-[#1a1a1a]">
          {onBack && (
            <button onClick={onBack} className="text-[10px] uppercase font-bold text-zinc-600 hover:text-amber-500 mb-4 transition-colors tracking-widest flex items-center gap-2">
              ← Return to Dashboard
            </button>
          )}
          <h2 className="text-xs font-black tracking-[0.3em] text-amber-500 uppercase flex items-center gap-2">
            <LucideGlobe size={16} />
            Digital Twin GMSS
          </h2>
        </div>
        
        <div className="flex-1 p-4 space-y-4">
          <div className="text-[9px] uppercase text-[#444] font-bold mb-2">Select Scenario</div>
          {[
            { id: "SUEZ_BLOCKAGE", label: "Suez Logistics Crisis", icon: <LucideLayers size={14} /> },
            { id: "CLIMATE_HEATWAVE", label: "Global Heatwave 2026", icon: <LucideAlertCircle size={14} /> },
            { id: "BANKING_LIQUIDITY", label: "Regional Banking Crunch", icon: <LucideActivity size={14} /> }
          ].map((s) => (
            <button
              key={s.id}
              onClick={() => runSimulation(s.id)}
              disabled={loading}
              className={`w-full text-left p-4 rounded border transition-all flex items-center gap-3 ${
                activeScenario === s.id && report ? "bg-amber-500/10 border-amber-500 text-amber-500" : "bg-[#111] border-[#1a1a1a] text-[#666] hover:border-[#333]"
              }`}
            >
              {s.icon}
              <span className="text-[10px] font-bold uppercase">{s.label}</span>
            </button>
          ))}
        </div>

        {macroBaselines && (
          <div className="p-6 bg-cyan-500/5 border-t border-[#1a1a1a]">
            <div className="text-[9px] uppercase text-cyan-500 font-bold mb-3 flex justify-between">
              <span>Macro Baseline</span>
              <span className="animate-pulse">● LIVE</span>
            </div>
            <div className="space-y-3 text-[9px] font-bold">
              <div className="flex justify-between">
                <span className="text-[#666]">INDIA VIX</span>
                <span className={macroBaselines.india_vix > 20 ? "text-red-400" : "text-green-400"}>{macroBaselines.india_vix.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#666]">INFLATION (CPI)</span>
                <span className="text-[#ccc]">{macroBaselines.inflation_cpi}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#666]">FII FLOW (CR)</span>
                <span className="text-cyan-400">₹{macroBaselines.fii_net_flow_cr}</span>
              </div>
            </div>
          </div>
        )}

        {report && (
          <div className="p-6 bg-amber-500/5 border-t border-[#1a1a1a]">
            <div className="text-[9px] uppercase text-amber-500 font-bold mb-2">Sim Metadata</div>
            <div className="space-y-2 text-[9px] text-[#888]">
              <div className="flex justify-between"><span>ID:</span> <span className="text-[#ccc]">{report?.simulation_id}</span></div>
              <div className="flex justify-between"><span>Shock:</span> <span className="text-[#ccc]">{((report?.shock?.initial_magnitude || 0) * 100).toFixed(0)}%</span></div>
              <div className="flex justify-between"><span>Impact:</span> <span className="text-[#ccc]">{report?.affected_sectors?.join(", ")}</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Main Simulation View */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center opacity-50 space-y-4">
            <LucidePlay size={48} className="text-amber-500 animate-pulse" />
            <div className="text-[10px] uppercase font-bold tracking-[0.4em]">Propagating Agent Beliefs...</div>
          </div>
        ) : report ? (
          <div className="p-8 space-y-8">
            {/* Header / Narrative */}
            <div className="bg-[#111] p-6 border-l-4 border-amber-500 rounded-r-lg">
              <h3 className="text-xl font-bold mb-2 uppercase italic">{report?.shock?.description || "Simulating Scenario..."}</h3>
              <p className="text-xs text-[#888] leading-relaxed">{report?.narrative_summary}</p>
            </div>

            {/* Visualizer Grid */}
            <div className="grid grid-cols-2 gap-8">
              {/* Supply Chain Dependency Graph (Mock Visualization) */}
              <div className="bg-[#0c0c0c] border border-[#1a1a1a] p-6 rounded-lg min-h-[300px] flex flex-col">
                <h4 className="text-[10px] font-bold uppercase mb-4 text-[#444] flex items-center gap-2">
                  <LucideShare2 size={14} />
                  Sector Stress Propagation
                </h4>
                <div className="flex-1 relative flex items-center justify-center">
                  {/* Mock Neo4j Graph elements */}
                  <div className="relative w-full h-full flex items-center justify-center">
                    <div className="absolute w-16 h-16 rounded-full border-2 border-red-500 bg-red-500/10 flex items-center justify-center text-[10px] font-bold">ENERGY</div>
                    <div className="absolute top-10 left-10 w-12 h-12 rounded-full border border-amber-500 bg-amber-500/10 flex items-center justify-center text-[8px] font-bold">LOGISTICS</div>
                    <div className="absolute bottom-10 right-10 w-12 h-12 rounded-full border border-zinc-600 flex items-center justify-center text-[8px] font-bold uppercase">RETAIL</div>
                    {/* Fake connection lines */}
                    <div className="absolute w-32 h-px bg-red-500/20 rotate-45" />
                    <div className="absolute w-32 h-px bg-amber-500/20 -rotate-45" />
                  </div>
                </div>
                <div className="mt-4 p-3 bg-zinc-900/50 rounded text-[9px] italic text-[#666]">
                  &gt; Non-linear stress detected in regional inter-dependencies...
                </div>
              </div>

              {/* Time-Series Impact */}
              <div className="bg-[#0c0c0c] border border-[#1a1a1a] p-6 rounded-lg flex flex-col">
                <h4 className="text-[10px] font-bold uppercase mb-4 text-[#444] flex items-center gap-2">
                  <LucideLineChart size={14} />
                  Economic Propagations
                </h4>
                <div className="flex-1 space-y-6">
                  {report?.propagation_steps?.slice(0, 5).map((step, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-[9px]">
                        <span className="text-[#888] uppercase">Step {step.step}: {step.target_sector}</span>
                        <span className={step.inflation_delta > 0.05 ? "text-red-400" : "text-green-400"}>
                          CPI Δ: +{step.inflation_delta.toFixed(2)}%
                        </span>
                      </div>
                      <div className="h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-amber-500" 
                          style={{ width: `${Math.abs(step.gdp_impact) * 20}%` }} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Agent Sentiment Tracker */}
            <div className="bg-[#0c0c0c] border border-[#1a1a1a] p-6 rounded-lg">
                <h4 className="text-[10px] font-bold uppercase mb-4 text-[#444] flex items-center gap-2">
                  <LucideActivity size={14} />
                  ABM Population Sentiment Monitor (5,000 Representative Agents)
                </h4>
                <div className="grid grid-cols-5 gap-4">
                    {["Bullish", "Neutral", "Anxious", "Panic", "Resilient"].map((label, i) => (
                        <div key={label} className="text-center p-3 border border-[#1a1a1a] rounded">
                            <div className="text-[10px] font-black italic mb-1">{label}</div>
                            <div className="text-lg font-bold text-amber-400">{Math.floor(Math.random() * 40) + 5}%</div>
                            <div className={`mt-2 h-0.5 w-full bg-[#1a1a1a]`}>
                                <div className="h-full bg-amber-500/30" style={{ width: `${Math.floor(Math.random() * 70) + 20}%` }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center opacity-20 space-y-4">
            <LucideGlobe size={64} className="animate-pulse" />
            <p className="text-xs uppercase tracking-widest">Select a Macro Scenario to begin Global Digital Twin Simulation</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Random helper for UI demo
function randomInt(min: number, max: number) {
    return Math.floor(Math.random() * (max - min + 1) + min);
}
