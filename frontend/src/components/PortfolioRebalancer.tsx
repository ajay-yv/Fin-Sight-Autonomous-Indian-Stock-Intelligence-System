"use client";

import { useState, useEffect } from "react";
import { LucideShieldCheck, LucideShieldAlert, LucideTrendingUp, LucideGlobe, LucideGavel } from "lucide-react";

interface PortfolioAsset {
  symbol: string;
  asset_class: "EQUITY" | "REAL_ESTATE" | "PRIVATE_CREDIT" | "COMMODITY" | "CASH";
  units: number;
  current_price: number;
  valuation: number;
  weight: number;
}

interface PortfolioState {
  portfolio_id: string;
  assets: PortfolioAsset[];
  total_valuation: number;
  target_weights: Record<string, number>;
  drift_score: number;
}

interface AgentProposal {
  agent_name: string;
  action: string;
  symbol: string;
  units: number;
  reasoning: string;
  tax_impact?: number;
  risk_impact?: number;
  esg_impact?: number;
}

interface NegotiationStep {
  step_index: number;
  proposals: AgentProposal[];
  consensus_reached: boolean;
  conflict_notes?: string;
}

interface AMAPRRunResult {
  run_id: string;
  initial_state: PortfolioState;
  final_state: PortfolioState;
  negotiation_history: NegotiationStep[];
  total_tax_optimized: number;
  risk_reduction: number;
  timestamp: string;
}

export default function PortfolioRebalancer() {
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [negotiation, setNegotiation] = useState<AMAPRRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    setFetchError(null);
    try {
      const res = await fetch(`${API_BASE}/api/amapr/portfolio`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPortfolio(data);
    } catch (err) {
      console.error("Failed to fetch portfolio", err);
      setFetchError("Backend unavailable — ensure the AMAPR service is running.");
    }
  };

  const handleSimulateRebalance = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/amapr/rebalance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await res.json();
      setNegotiation(data);
    } catch (err) {
      console.error("Negotiation failed", err);
    } finally {
      setLoading(false);
    }
  };

  if (fetchError) {
    return (
      <div className="p-8 font-mono text-xs text-red-600 flex flex-col items-center gap-3">
        <span className="text-2xl">⚠</span>
        <p className="font-bold uppercase">{fetchError}</p>
        <button onClick={fetchPortfolio} className="border border-red-400 px-4 py-1 uppercase text-[10px] hover:bg-red-50 transition-colors">
          Retry Connection
        </button>
      </div>
    );
  }

  if (!portfolio) return <div className="p-8 font-mono text-xs opacity-50 animate-pulse">Initializing Portfolio Engine...</div>;

  const totalVal = portfolio.total_valuation;

  return (
    <div className="flex flex-col h-full bg-[#fdfdfc] text-[var(--color-war-text)]">
      {/* Header */}
      <div className="p-6 border-b border-[var(--color-war-border)] flex justify-between items-center">
        <div>
          <h2 className="font-serif text-2xl font-black italic uppercase tracking-tight">AMAPR Agentic Engine</h2>
          <p className="font-mono text-[10px] uppercase text-[#888]">LangGraph Multi-Agent Portfolio Rebalancer</p>
        </div>
        <div className="text-right">
          <div className="font-serif text-xl font-bold">₹{totalVal.toLocaleString()}</div>
          <div className="font-mono text-[9px] uppercase text-[var(--color-war-buy)]">Unified AUM (Equity + RWA)</div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex">
        {/* Left: Portfolio View */}
        <div className="w-1/2 border-r border-[var(--color-war-border)] p-6 overflow-y-auto">
          <div className="flex items-center gap-2 mb-6 border-b border-[var(--color-war-text)] pb-2">
            <LucideGlobe size={16} />
            <h3 className="font-mono text-xs font-bold uppercase tracking-widest">Current Holdings</h3>
          </div>

          <div className="space-y-4">
            {portfolio.assets.map(asset => (
              <div key={asset.symbol} className="border border-[var(--color-war-border)] p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className={`px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase ${asset.asset_class !== "EQUITY" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}>
                      {asset.asset_class}
                    </span>
                    <h4 className="font-serif text-lg font-bold mt-1">{asset.symbol}</h4>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-xs font-bold">₹{asset.valuation.toLocaleString()}</div>
                    <div className="font-mono text-[9px] text-[#888]">{asset.units} Units</div>
                  </div>
                </div>
                <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--color-war-text)]" style={{ width: `${(asset.valuation / totalVal) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>

          <button 
            onClick={handleSimulateRebalance}
            disabled={loading}
            className="mt-8 w-full bg-[var(--color-war-text)] text-white font-mono text-xs py-3 uppercase tracking-widest hover:bg-black transition-colors disabled:opacity-50"
          >
            {loading ? "Negotiating Fiduciary Consensus..." : "Trigger Multi-Agent Rebalance"}
          </button>
        </div>

        {/* Right: Negotiation Visualizer */}
        <div className="w-1/2 p-6 bg-[#F5F2EC] overflow-y-auto">
          <div className="flex items-center gap-2 mb-6 border-b border-[var(--color-war-text)] pb-2">
            <LucideGavel size={16} />
            <h3 className="font-mono text-xs font-bold uppercase tracking-widest">Agentic Negotiation Flow</h3>
          </div>

          {!negotiation ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-40">
              <LucideShieldCheck size={48} className="mb-4" />
              <p className="font-serif italic text-sm">Awaiting simulation to trigger LangGraph consensus protocol...</p>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Negotiation Steps */}
              {negotiation.negotiation_history.map((step, sIdx) => (
                <div key={sIdx} className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-black text-white text-[10px] flex items-center justify-center font-bold">
                      {step.step_index}
                    </div>
                    <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#888]">
                      Stage {step.step_index}: Multi-Agent Review
                    </span>
                  </div>
                  
                  <div className="space-y-3 pl-8">
                    {step.proposals.map((prop, pIdx) => (
                      <div key={pIdx} className="bg-white border border-[var(--color-war-border)] p-3 shadow-sm relative overflow-hidden">
                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${prop.action === "BUY" ? "bg-green-500" : prop.action === "SELL" ? "bg-red-500" : "bg-gray-300"}`} />
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-mono text-[9px] font-black p-0.5 bg-gray-100 rounded">{prop.agent_name}</span>
                          <span className={`font-mono text-[9px] font-bold ${prop.action === "BUY" ? "text-green-600" : prop.action === "SELL" ? "text-red-600" : "text-gray-500"}`}>
                            {prop.action} {prop.units} {prop.symbol}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#666] leading-tight italic">"{prop.reasoning}"</p>
                        
                        {(prop.tax_impact || prop.esg_impact) && (
                          <div className="mt-2 flex gap-3 border-t border-gray-50 pt-1.5">
                            {prop.tax_impact && <span className="font-mono text-[8px] text-green-600 uppercase">Tax Offset: ₹{prop.tax_impact.toLocaleString()}</span>}
                            {prop.esg_impact && <span className="font-mono text-[8px] text-blue-600 uppercase">ESG Alignment: {prop.esg_impact > 0 ? "PASSED" : "VETOED"}</span>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {/* Final Synthesis */}
              <div className="pt-6 border-t border-[var(--color-war-border)]">
                <div className="bg-black text-white p-4">
                  <h4 className="font-mono text-[10px] font-bold uppercase mb-2 text-[#aaa]">Final Rebalance Synthesis</h4>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs">Tax Capital Saved</span>
                    <span className="font-mono text-xs font-bold text-green-400">₹{negotiation.total_tax_optimized.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs">Risk Reduction</span>
                    <span className="font-mono text-xs font-bold text-blue-400">{(negotiation.risk_reduction * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
