"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import * as api from "@/lib/api";

export default function HomePage() {
  const [symbolInput, setSymbolInput] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleStartAnalysis = async () => {
    // ── Smart Extraction: find potential tickers in messy text ──────
    const TICKER_PATTERN = /\b[A-Z0-9&.\-]{1,15}(\.NS|\.BO)?\b/g;
    const UNIT_PATTERN = /([\d,.]+)\s*Units/i;
    const VALUE_PATTERN = /₹\s*([\d,.]+)/;
    
    let symbols: string[] = [];
    let portfolioAssets: any[] = [];
    
    // Split by common separators if present
    const lines = symbolInput.split(/\n|,/);
    
    let currentAsset: any = null;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      const tickerMatch = trimmed.toUpperCase().match(TICKER_PATTERN);
      if (tickerMatch) {
        // If we found a new ticker, push previous one and start new
        if (currentAsset?.symbol) portfolioAssets.push(currentAsset);
        currentAsset = { symbol: tickerMatch[0], asset_class: "EQUITY" };
        symbols.push(tickerMatch[0]);
      } else if (currentAsset) {
        const unitMatch = trimmed.match(UNIT_PATTERN);
        const valueMatch = trimmed.match(VALUE_PATTERN);
        
        if (unitMatch) {
          currentAsset.units = parseFloat(unitMatch[1].replace(/,/g, ""));
        } else if (valueMatch) {
          currentAsset.valuation = parseFloat(valueMatch[1].replace(/,/g, ""));
          currentAsset.current_price = currentAsset.valuation / (currentAsset.units || 1);
        } else if (["EQUITY", "REAL_ESTATE", "COMMODITY", "CASH"].includes(trimmed.toUpperCase())) {
          currentAsset.asset_class = trimmed.toUpperCase();
        }
      }
    }
    if (currentAsset?.symbol) portfolioAssets.push(currentAsset);

    // Filter and Deduplicate Symbols
    symbols = Array.from(new Set(symbols))
      .filter((s) => /^[A-Z0-9&.\-]{2,20}$/.test(s))
      .slice(0, 5);

    if (symbols.length === 0) {
      setError("Enter at least one stock symbol to proceed.");
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      // ── Sync Portfolio if advanced data was found ──────────────────
      if (portfolioAssets.length > 0 && portfolioAssets.some(a => a.units)) {
        console.log("Syncing extracted portfolio assets...", portfolioAssets);
        const totalVal = portfolioAssets.reduce((sum, a) => sum + (a.valuation || 0), 0);
        
        await fetch(`/api/amapr/portfolio`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            portfolio_id: "P-USER",
            assets: portfolioAssets.map(a => ({
              symbol: a.symbol,
              asset_class: a.asset_class || "EQUITY",
              units: a.units || 0,
              current_price: a.current_price || 0,
              valuation: a.valuation || 0,
              weight: totalVal > 0 ? (a.valuation || 0) / totalVal : 0
            })),
            total_valuation: totalVal,
            target_weights: { EQUITY: 0.6, REAL_ESTATE: 0.2, PRIVATE_CREDIT: 0.1, CASH: 0.1 },
            drift_score: 0.1
          })
        });
      }

      const { run_id } = await api.startAnalysis(symbols);
      router.push(`/run/${run_id}`);
    } catch (startErr) {
      setError(
        startErr instanceof Error
          ? startErr.message
          : "Failed to initialize terminal routine"
      );
      setIsStarting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl border border-[var(--color-war-border)] bg-white p-8">
        <h1 className="text-3xl font-serif font-bold text-[var(--color-war-text)] mb-2 uppercase tracking-wide">
          Intelligence Terminal
        </h1>
        <p className="text-sm font-mono text-[var(--color-war-muted)] mb-8 uppercase tracking-widest border-b border-[var(--color-war-border)] pb-4">
          Awaiting input parameters...
        </p>

        <div className="space-y-4">
          <div>
            <label
              htmlFor="symbolInput"
              className="block text-xs font-mono font-bold text-[var(--color-war-text)] mb-2 uppercase tracking-widest"
            >
              Target Assets (NSE Symbols)
            </label>
            <input
              id="symbolInput"
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isStarting) {
                  handleStartAnalysis();
                }
              }}
              placeholder="RELIANCE, TCS, HDFCBANK"
              className="w-full bg-transparent border border-[var(--color-war-border)] px-4 py-3 font-mono text-[var(--color-war-text)] placeholder-[var(--color-war-muted)] focus:outline-none focus:border-[var(--color-war-text)] transition-colors"
            />
            <p className="text-[10px] font-mono text-[var(--color-war-muted)] mt-2 uppercase tracking-widest">
              Limit: 5 Assets per run. Comma-separated.
            </p>
          </div>

          <button
            onClick={handleStartAnalysis}
            disabled={isStarting}
            className="w-full mt-6 bg-[var(--color-war-text)] hover:bg-[#333] disabled:bg-[var(--color-war-muted)] disabled:cursor-not-allowed text-white font-mono font-bold uppercase tracking-widest py-4 transition-colors cursor-pointer"
          >
            {isStarting ? "Initializing..." : "Initiate Protocol"}
          </button>

          {error && (
            <div className="mt-4 border border-[var(--color-war-sell)] bg-red-50 p-3">
              <p className="text-xs font-mono text-[var(--color-war-sell)] font-bold uppercase tracking-widest">
                [ERROR] {error}
              </p>
            </div>
          )}
        </div>
      </div>
      
      <footer className="mt-12 text-center text-[10px] font-mono text-[var(--color-war-muted)] uppercase tracking-wider">
        System active. Unauthorized access logged.
      </footer>
    </div>
  );
}
