"use client";

import { useState, useEffect } from "react";

interface RWAAsset {
  asset_id: string;
  asset_type: string;
  name: string;
  token_price: number;
  annual_yield: number;
  liquidity_score: number;
  on_chain_address: string;
  valuation_source: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ASSET_TYPE_COLORS: Record<string, string> = {
  real_estate: "#4F46E5", // indigo
  private_credit: "#059669", // emerald
  commodities: "#D97706", // amber
  art: "#DB2777", // pink
};

const ASSET_TYPE_LABELS: Record<string, string> = {
  real_estate: "Real Estate",
  private_credit: "Private Credit",
  commodities: "Commodities",
  art: "Art",
};

function LiquidityBar({ score }: { score: number }) {
  const percent = Math.round(score * 100);
  const color =
    score >= 0.7 ? "#10b981" : score >= 0.35 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${percent}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-[10px] text-gray-500 w-8">{percent}%</span>
    </div>
  );
}

export default function RWAHeatmap() {
  const [rwas, setRwas] = useState<RWAAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<RWAAsset | null>(null);

  useEffect(() => {
    fetch(`/api/rwa/list`)
      .then((r) => r.json())
      .then((data) => {
        setRwas(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        // Mock data for frontend demo if backend is not wired
        setRwas([
          {
            asset_id: "RWA_BLR_OFFICE_01",
            asset_type: "real_estate",
            name: "Bangalore Premium Office Space",
            token_price: 1250.45,
            annual_yield: 0.082,
            liquidity_score: 0.45,
            on_chain_address: "0x71C...aB2",
            valuation_source: "ZONIQX_VERIFIED",
          },
          {
            asset_id: "RWA_MUM_WH_02",
            asset_type: "real_estate",
            name: "Mumbai Grade-A Warehouse",
            token_price: 540.2,
            annual_yield: 0.095,
            liquidity_score: 0.3,
            on_chain_address: "0x82D...3C4",
            valuation_source: "ZONIQX_VERIFIED",
          },
          {
            asset_id: "RWA_CREDIT_SME_IND",
            asset_type: "private_credit",
            name: "Indian MSME Credit Pool",
            token_price: 10.0,
            annual_yield: 0.14,
            liquidity_score: 0.15,
            on_chain_address: "0x93E...4D5",
            valuation_source: "ZONIQX_VERIFIED",
          },
          {
            asset_id: "RWA_GOLD_DGL_01",
            asset_type: "commodities",
            name: "Pax Gold Digital Proxy",
            token_price: 6400.0,
            annual_yield: 0.0,
            liquidity_score: 0.95,
            on_chain_address: "0xA4F...5E6",
            valuation_source: "ZONIQX_VERIFIED",
          },
        ]);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-6 font-mono text-xs text-[var(--color-war-muted)] uppercase animate-pulse">
        Loading RWA Universe...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#fdfdfc]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--color-war-border)]">
        <h3 className="font-serif text-lg font-black italic uppercase tracking-tight">
          RWA Universe Heatmap
        </h3>
        <p className="font-mono text-[9px] uppercase text-[#888] tracking-widest">
          Tokenized Real-World Assets · Zoniqx TPaaS · On-Chain Verified
        </p>
      </div>

      {/* Grid */}
      <div className="p-4 grid grid-cols-2 gap-3 overflow-y-auto flex-1">
        {rwas.map((rwa) => {
          const color =
            ASSET_TYPE_COLORS[rwa.asset_type] || "#6B7280";
          const isSelected = selected?.asset_id === rwa.asset_id;

          return (
            <div
              key={rwa.asset_id}
              onClick={() => setSelected(isSelected ? null : rwa)}
              className={`border-2 p-3 cursor-pointer transition-all duration-200 ${
                isSelected
                  ? "shadow-lg scale-[1.02]"
                  : "hover:shadow-md hover:scale-[1.01]"
              }`}
              style={{ borderColor: isSelected ? color : "#e0dbd0" }}
            >
              {/* Asset Type Badge */}
              <div className="flex justify-between items-start mb-2">
                <span
                  className="font-mono text-[8px] uppercase px-1.5 py-0.5 text-white"
                  style={{ backgroundColor: color }}
                >
                  {ASSET_TYPE_LABELS[rwa.asset_type] || rwa.asset_type}
                </span>
                <span className="font-mono text-[9px] text-[#888]">
                  {(rwa.annual_yield * 100).toFixed(1)}% yield
                </span>
              </div>

              {/* Name */}
              <h4 className="font-serif text-sm font-bold leading-tight mb-2 line-clamp-2">
                {rwa.name}
              </h4>

              {/* Price */}
              <div className="font-mono text-base font-bold mb-2">
                ₹{rwa.token_price.toLocaleString()}
                <span className="text-[10px] font-normal text-[#888] ml-1">/ token</span>
              </div>

              {/* Liquidity */}
              <div className="mb-1">
                <p className="font-mono text-[8px] uppercase text-[#888] mb-1">
                  Liquidity Score
                </p>
                <LiquidityBar score={rwa.liquidity_score} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail Panel */}
      {selected && (
        <div
          className="border-t-2 p-4 bg-[#F5F2EC]"
          style={{
            borderColor:
              ASSET_TYPE_COLORS[selected.asset_type] || "#6B7280",
          }}
        >
          <div className="font-mono text-[10px] uppercase text-[#888] mb-1">
            On-Chain Details
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div>
              <span className="text-[#888]">Address: </span>
              <span className="font-bold">{selected.on_chain_address}</span>
            </div>
            <div>
              <span className="text-[#888]">Source: </span>
              <span className="font-bold text-green-700">
                ✓ {selected.valuation_source}
              </span>
            </div>
            <div>
              <span className="text-[#888]">Annual Yield: </span>
              <span className="font-bold">
                {(selected.annual_yield * 100).toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-[#888]">Liquidity: </span>
              <span
                className={`font-bold ${
                  selected.liquidity_score >= 0.7
                    ? "text-green-700"
                    : selected.liquidity_score >= 0.35
                    ? "text-amber-600"
                    : "text-red-600"
                }`}
              >
                {selected.liquidity_score >= 0.7
                  ? "HIGH"
                  : selected.liquidity_score >= 0.35
                  ? "MEDIUM"
                  : "LOW"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
