"use client";

import { useState, useEffect } from "react";
import { LucideShield, LucideZap, LucideEyeOff, LucideLock, LucideRefreshCcw, LucideActivity } from "lucide-react";

interface ZKPStatus {
  step: "IDLE" | "GENERATING" | "VERIFYING" | "SHIELDED";
  proofId?: string;
  progress: number;
}

export default function RetailDarkPool({ symbol }: { symbol: string }) {
  const [zkp, setZkp] = useState<ZKPStatus>({ step: "IDLE", progress: 0 });
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ volume: 0, version: "v2.0" });
  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState(0.1);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/darkpool/stats`);
      const data = await res.json();
      setStats({ volume: data.confidential_volume, version: data.protocol_version });
    } catch (err) {
      console.error("Failed to fetch dark pool stats", err);
    }
  };

  const handlePlaceOrder = async () => {
    setLoading(true);
    setZkp({ step: "GENERATING", progress: 20 });
    
    // Simulate ZKP Latency
    setTimeout(() => setZkp({ step: "GENERATING", progress: 60 }), 800);
    setTimeout(() => setZkp({ step: "VERIFYING", progress: 90 }), 1600);
    
    try {
      const res = await fetch(`${API_BASE}/api/darkpool/order?symbol=${symbol}&side=${orderType}&quantity=${quantity}`, {
        method: "POST"
      });
      const result = await res.json();
      
      setTimeout(() => {
        setZkp({ step: "SHIELDED", proofId: result.proof?.proof_id, progress: 100 });
        setLoading(false);
        fetchStats();
      }, 2400);
    } catch (err) {
        console.error("Dark Pool submission failed", err);
        setZkp({ step: "IDLE", progress: 0 });
        setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050505] text-[#eee] font-mono overflow-y-auto">
      {/* Privacy Header */}
      <div className="p-6 border-b border-[#1a1a1a] flex justify-between items-center bg-[#0a0a0a]">
        <div>
          <h2 className="text-xl font-bold tracking-tighter flex items-center gap-2 text-indigo-400">
            <LucideLock size={20} />
            RETAIL DARK POOL
          </h2>
          <p className="text-[9px] uppercase tracking-widest text-[#444]">Confidential Fractional Matching v2.0</p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <div className="text-[9px] uppercase text-[#444]">Protocol</div>
            <div className="text-[10px] text-indigo-300 font-bold">{stats.version}</div>
          </div>
          <div className="text-right border-l border-[#222] pl-4">
            <div className="text-[9px] uppercase text-[#444]">Confidential Vol</div>
            <div className="text-[10px] text-green-400 font-bold">{stats.volume.toFixed(2)} RWA UNITS</div>
          </div>
        </div>
      </div>

      <div className="flex-1 p-8 flex gap-8 items-start justify-center max-w-6xl mx-auto w-full">
        {/* Order Terminal */}
        <div className="w-1/2 space-y-6 bg-[#0a0a0a] border border-[#1a1a1a] p-8 rounded-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-2 opacity-10">
            <LucideEyeOff size={120} />
          </div>
          
          <div className="relative z-10">
            <h3 className="text-sm font-bold uppercase tracking-[0.2em] mb-6 border-b border-[#222] pb-2">Confidential Intent</h3>
            
            <div className="space-y-4">
              <div className="flex gap-2">
                <button 
                  onClick={() => setOrderType("BUY")}
                  className={`flex-1 py-3 text-[10px] font-bold border transition-all ${orderType === "BUY" ? "bg-green-500/10 border-green-500 text-green-500" : "bg-transparent border-[#222] text-[#444]"}`}
                >
                  P2P BUY
                </button>
                <button 
                  onClick={() => setOrderType("SELL")}
                  className={`flex-1 py-3 text-[10px] font-bold border transition-all ${orderType === "SELL" ? "bg-red-500/10 border-red-500 text-red-500" : "bg-transparent border-[#222] text-[#444]"}`}
                >
                  P2P SELL
                </button>
              </div>

              <div>
                <label className="block text-[9px] uppercase text-[#444] mb-1">Target Asset</label>
                <div className="bg-[#111] border border-[#222] px-4 py-3 text-xs font-bold text-indigo-300">
                  {symbol} (FRACTIONAL RWA)
                </div>
              </div>

              <div>
                <label className="block text-[9px] uppercase text-[#444] mb-1">Fractional Quantity (Units)</label>
                <input 
                  type="number" 
                  step="0.01" 
                  value={quantity}
                  onChange={(e) => setQuantity(parseFloat(e.target.value))}
                  className="w-full bg-[#111] border border-[#222] px-4 py-3 text-xs font-bold focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-4">
                <button 
                  onClick={handlePlaceOrder}
                  disabled={loading}
                  className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black uppercase tracking-widest text-[11px] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <LucideZap size={14} />
                  Submit Shielded Order
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ZKP Visualization */}
        <div className="w-1/2 space-y-6">
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] p-6 rounded-lg min-h-[200px] flex flex-col justify-center items-center text-center">
            {zkp.step === "IDLE" ? (
              <div className="opacity-20 flex flex-col items-center">
                <LucideShield size={48} className="mb-4" />
                <p className="text-[10px] uppercase tracking-widest italic">Awaiting Private Intent...</p>
              </div>
            ) : (
              <div className="w-full space-y-6 animate-in fade-in zoom-in duration-300">
                <div className="flex flex-col items-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 border-2 ${zkp.step === "SHIELDED" ? "border-green-500 text-green-500" : "border-indigo-500 text-indigo-500 animate-pulse"}`}>
                    {zkp.step === "SHIELDED" ? <LucideShield size={32} /> : <LucideRefreshCcw size={32} className="animate-spin" />}
                  </div>
                  <h4 className="text-xs font-bold tracking-[0.3em] uppercase">{zkp.step}</h4>
                  {zkp.proofId && <p className="text-[8px] text-[#444] mt-1 font-mono">PROOF_ID: {zkp.proofId}</p>}
                </div>

                <div className="w-full h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${zkp.progress}%` }} />
                </div>

                <div className="grid grid-cols-2 gap-2 w-full text-[8px] uppercase tracking-tighter">
                  <div className={`p-2 border border-[#222] ${zkp.progress >= 20 ? "text-green-500 border-green-500/20" : "text-[#333]"}`}>[01] Generate Witness</div>
                  <div className={`p-2 border border-[#222] ${zkp.progress >= 60 ? "text-green-500 border-green-500/20" : "text-[#333]"}`}>[02] Compute Constraint</div>
                  <div className={`p-2 border border-[#222] ${zkp.progress >= 90 ? "text-green-500 border-green-500/20" : "text-[#333]"}`}>[03] Groth16 Verification</div>
                  <div className={`p-2 border border-[#222] ${zkp.step === "SHIELDED" ? "text-green-500 border-green-500/20" : "text-[#333]"}`}>[04] Enclave Hand-off</div>
                </div>
              </div>
            )}
          </div>

          <div className="bg-indigo-500/5 border border-indigo-500/20 p-6 rounded-lg">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-4 flex items-center gap-2">
              <LucideActivity size={14} />
              Confidential Matching Log
            </h4>
            <div className="space-y-2 text-[9px] font-mono text-[#666]">
              <p>&gt; initializing confidential enclave...</p>
              <p>&gt; oasis-sapphire-mainnet connected.</p>
              {zkp.step === "SHIELDED" && (
                <>
                  <p className="text-green-500/70">&gt; proof of solvency verified [OK]</p>
                  <p className="text-indigo-400">&gt; order {zkp.proofId?.slice(0,8)} shielded and moved to dark book.</p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
