const NEXT_PUBLIC_API_URL = "/api";
const runId = "dd32319c-9d94-4fd5-9c34-efb1034d1e97";
const normalizedSymbol = "RELIANCE";

const API_BASE_URL = NEXT_PUBLIC_API_URL || "";
const endpoint = `${API_BASE_URL}/run/${runId}/stock/${encodeURIComponent(normalizedSymbol)}/ohlcv`;

console.log("Endpoint:", endpoint);
