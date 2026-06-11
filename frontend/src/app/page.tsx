"use client";

import { useState, useEffect, useRef } from "react";
import { useMarketIndices } from "@/lib/api-hooks";
import { motion, useInView, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StockData {
  symbol: string;
  company: string;
  ltp: string;
  change: number;
  sentiment: number;
  sentiment_type: "bull" | "neut" | "bear";
  confidence: number;
  catalyst: string;
}

// Fallback data for initial load
const FALLBACK_HOTLIST_DATA: StockData[] = [
  {
    symbol: "RELIANCE",
    company: "Reliance Industries",
    ltp: "₹2,954.20",
    change: 1.2,
    sentiment: 85,
    sentiment_type: "bull",
    confidence: 92,
    catalyst: "Strong Q3 retail margins beat consensus.",
  },
  {
    symbol: "TCS",
    company: "Tata Consultancy",
    ltp: "₹4,120.50",
    change: -0.5,
    sentiment: 45,
    sentiment_type: "neut",
    confidence: 88,
    catalyst: "US client discretionary spend remains muted.",
  },
  {
    symbol: "HDFCBANK",
    company: "HDFC Bank Ltd.",
    ltp: "₹1,432.80",
    change: 2.1,
    sentiment: 72,
    sentiment_type: "bull",
    confidence: 95,
    catalyst: "Deposit growth accelerates post-merger integration.",
  },
  {
    symbol: "INFY",
    company: "Infosys Ltd.",
    ltp: "₹1,642.10",
    change: -1.4,
    sentiment: 32,
    sentiment_type: "bear",
    confidence: 81,
    catalyst: "Margin pressure guidance lower than street.",
  },
];

const AGENTS = [
  {
    icon: "forum",
    title: "Sentiment Agent",
    status: "ACTIVE",
    description:
      "Scans thousands of news sources, social feeds, and earnings transcripts for emotional polarity.",
    color: "google-blue",
  },
  {
    icon: "candlestick_chart",
    title: "Technical Agent",
    status: "ACTIVE",
    description:
      "Analyzes price action, volume profiles, and momentum indicators in real-time.",
    color: "google-green",
  },
  {
    icon: "description",
    title: "Filing Verification",
    status: "ACTIVE",
    description:
      "Cross-references sentiment claims against SEC/BSE official corporate filings to hallucination-proof insights.",
    color: "google-yellow",
  },
];

export default function Home() {
  const { data: indicesData, isLoading, error } = useMarketIndices();
  const [hotlistData, setHotlistData] = useState<StockData[]>(
    FALLBACK_HOTLIST_DATA,
  );

  // Update hotlist when API data arrives
  useEffect(() => {
    if (indicesData?.indices) {
      // You can map API data here if needed
      console.log("Market indices loaded:", indicesData);
    }
  }, [indicesData]);

  return (
    <div className="w-full">
      {/* Hero Section with scroll animation */}
      <HeroSection />

      {/* AI Research Terminal (Search) */}
      <SearchTerminal />

      {/* Market Pulse Dashboard */}
      <MarketDashboard isLoading={isLoading} />

      {/* AI Hotlist & Orchestration */}
      <HotlistSection hotlistData={hotlistData} />
    </div>
  );
}

// Hero Section Component
function HeroSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });

  return (
    <motion.section
      ref={ref}
      className="relative w-full pt-24 pb-32 px-6 md:px-10 overflow-hidden bg-grid-pattern"
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.8 }}
    >
      {/* Immersive Data Pulse Background */}
      <div className="absolute inset-0 pointer-events-none opacity-30">
        {[10, 30, 50, 70, 90].map((position, idx) => (
          <motion.div
            key={`line-${idx}`}
            className="data-line"
            style={{
              position: "absolute",
              width: "1px",
              left: `${position}%`,
              height: 150 + idx * 28,
              background:
                "linear-gradient(to bottom, transparent, rgba(66, 133, 244, 0.5), transparent)",
              animation: `pulse-line 4s infinite linear ${idx * 0.5}s`,
            }}
          />
        ))}
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-r from-google-blue/10 via-google-red/5 to-google-yellow/5 rounded-full blur-[100px] pointer-events-none"
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 4, repeat: Infinity }}
      />

      <div className="max-w-[1400px] mx-auto flex flex-col items-center text-center relative z-10">
        <motion.div
          className="inline-flex items-center gap-2 bg-surface-container-lowest/80 backdrop-blur-sm px-4 py-1.5 rounded-full border border-outline-variant/30 mb-8 shadow-sm"
          initial={{ opacity: 0, y: -20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <span className="material-symbols-outlined text-google-blue text-sm symbol-filled">
            auto_awesome
          </span>
          <span className="font-label-lg text-label-lg text-on-surface">
            Sentinews.AI
          </span>
        </motion.div>

        <motion.h1
          className="font-headline-lg text-3xl md:text-5xl font-bold tracking-tight mb-6 max-w-5xl leading-tight"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-google-blue via-google-red to-google-yellow">
            Sentinews AI
          </span>{" "}
          <br />
          <span className="text-on-surface">AI Financial Intelligence</span>
        </motion.h1>

        <motion.p
          className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          Real-time institutional-grade stock analysis powered by autonomous AI
          research agents. Gain clarity in volatile markets with continuous data
          synthesis.
        </motion.p>

        <motion.div
          className="flex flex-col sm:flex-row gap-4 items-center"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          <motion.button
            className="bg-google-blue text-white px-8 py-3.5 rounded-full font-label-lg text-label-lg flex items-center gap-2 shadow-[0_0_20px_rgba(66,133,244,0.3)]"
            whileHover={{
              scale: 1.05,
              boxShadow: "0_0_30px_rgba(66,133,244,0.5)",
            }}
            whileTap={{ scale: 0.98 }}
          >
            Start Research
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </motion.button>
          <motion.button
            className="glass-card text-on-surface px-8 py-3.5 rounded-full font-label-lg text-label-lg border border-outline-variant/50"
            whileHover={{ scale: 1.05, borderColor: "rgb(66, 133, 244)" }}
            whileTap={{ scale: 0.98 }}
          >
            View Sample Report
          </motion.button>
        </motion.div>
      </div>
    </motion.section>
  );
}

// Search Terminal Component
function SearchTerminal() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  const QUICK_QUERIES = [
    {
      icon: "summarize",
      label: "Earnings calls analysis",
      query: "Analyze earnings call results for top Indian IT companies",
    },
    {
      icon: "memory",
      label: "Tech sector outlook",
      query: "What is the outlook for the Indian tech sector?",
    },
    {
      icon: "account_balance",
      label: "Fed rate impact",
      query: "How does the US Fed rate decision impact Indian markets?",
    },
  ];

  const handleSubmit = async (q?: string) => {
    const searchQuery = q || query;
    if (!searchQuery.trim() || isLoading) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/research/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: searchQuery }),
        },
      );
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "";
      setError(
        message ||
          "Failed to connect to the research engine. Is the backend running?",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <motion.section
      ref={ref}
      className="w-full px-6 md:px-10 -mt-24 relative z-20 mb-20"
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-4xl mx-auto">
        {/* Search Box */}
        <motion.div
          className="glass-card rounded-3xl p-3 border border-white/10 shadow-2xl flex items-center gap-3 relative overflow-hidden group"
          whileHover={{ borderColor: "rgba(66, 133, 244, 0.5)" }}
          animate={isLoading ? { borderColor: "rgba(66, 133, 244, 0.6)" } : {}}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-google-blue/10 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
          <span className="material-symbols-outlined text-google-blue ml-4 text-2xl flex-shrink-0">
            {isLoading ? "hourglass_top" : "search"}
          </span>
          <input
            id="research-query-input"
            className="w-full bg-transparent border-none text-on-surface focus:ring-0 font-body-lg text-lg placeholder-on-surface-variant/50 py-4 outline-none"
            placeholder="Ask anything about stocks, sectors, or macro trends..."
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <motion.button
            id="research-submit-btn"
            className="bg-google-blue text-white p-3 rounded-2xl mr-1 shadow-inner flex-shrink-0 disabled:opacity-50"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleSubmit()}
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? (
              <motion.span
                className="material-symbols-outlined text-white"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                autorenew
              </motion.span>
            ) : (
              <span className="material-symbols-outlined text-white">
                arrow_forward
              </span>
            )}
          </motion.button>
        </motion.div>

        {/* Quick Query Chips */}
        <motion.div
          className="flex flex-wrap gap-3 mt-6 justify-center"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {QUICK_QUERIES.map((item, idx) => (
            <motion.button
              key={item.icon}
              id={`quick-query-${idx}`}
              className="glass-card px-5 py-2.5 rounded-xl border border-surface-container-highest text-on-surface-variant font-label-sm text-sm flex items-center gap-2"
              whileHover={{
                scale: 1.05,
                borderColor: "rgba(66, 133, 244, 0.5)",
                color: "white",
              }}
              whileTap={{ scale: 0.95 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => {
                setQuery(item.query);
                handleSubmit(item.query);
              }}
              disabled={isLoading}
            >
              <span className="material-symbols-outlined text-[18px]">
                {item.icon}
              </span>
              {item.label}
            </motion.button>
          ))}
        </motion.div>

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 glass-card rounded-2xl p-5 border border-danger/40 bg-danger/5"
          >
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-danger text-xl flex-shrink-0">
                error
              </span>
              <div>
                <p className="text-danger font-semibold text-sm mb-1">
                  Research Engine Error
                </p>
                <p className="text-on-surface-variant text-sm">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Loading State */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 glass-card rounded-2xl p-6 border border-google-blue/30"
          >
            <div className="flex items-center gap-4">
              <motion.div
                className="w-10 h-10 rounded-full border-2 border-google-blue border-t-transparent"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
              <div>
                <p className="text-on-surface font-semibold text-sm">
                  Multi-Agent Research Running...
                </p>
                <p className="text-on-surface-variant text-xs mt-0.5">
                  Fetching news · Analyzing fundamentals · Synthesizing report
                </p>
              </div>
            </div>
            {/* Progress dots */}
            <div className="flex gap-2 mt-4">
              {[
                "Sentiment Agent",
                "Technical Agent",
                "Filing Verification",
              ].map((agent, i) => (
                <motion.div
                  key={agent}
                  className="flex items-center gap-1.5 text-xs text-on-surface-variant bg-surface-container-high/50 px-3 py-1.5 rounded-full"
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.4,
                  }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-google-blue" />
                  {agent}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Result Panel */}
        {Boolean(result) && !isLoading && (
          <ResearchReportPanel
            result={result}
            onClose={() => setResult(null)}
          />
        )}
      </div>
    </motion.section>
  );
}

// ============================================================
// HELPERS — Markdown / Text Parser
// ============================================================

function cleanText(raw: string): string {
  if (!raw) return "";
  return raw.replace(/\\n/g, "\n");
}

function parsePrice(val: string): number {
  if (!val) return 0;
  const numbers = val.replace(/,/g, "").match(/\d+(\.\d+)?/g);
  if (numbers && numbers.length > 0) {
    if (numbers.length >= 2) {
      return (parseFloat(numbers[0]) + parseFloat(numbers[1])) / 2;
    }
    return parseFloat(numbers[0]);
  }
  return 0;
}

function extractKeyStats(text: string) {
  const stats: { name: string; value: string }[] = [];
  if (!text) return stats;

  const cleaned = cleanText(text);
  const rows = cleaned.split("\n");
  console.log("ROWS =", rows);

  for (const row of rows) {
    console.log("ROW =", row);
    if (
      row.includes("|") &&
      !row.toLowerCase().includes("metric") &&
      !row.includes("---")
    ) {
      const parts = row
        .split("|")
        .map((p) => p.trim())
        .filter((p) => p !== "");
      if (parts.length >= 2) {
        const name1 = parts[0].replace(/\*\*/g, "").trim();
        const val1 = parts[1].trim();
        if (
          name1 &&
          val1 &&
          val1 !== "-" &&
          !val1.toLowerCase().includes("[value]")
        ) {
          stats.push({ name: name1, value: val1 });
        }
      }
      if (parts.length >= 4) {
        const name2 = parts[2].replace(/\*\*/g, "").trim();
        const val2 = parts[3].trim();
        if (
          name2 &&
          val2 &&
          val2 !== "-" &&
          !val2.toLowerCase().includes("[value]")
        ) {
          stats.push({ name: name2, value: val2 });
        }
      }
    }
  }

  // Fallbacks
  if (stats.length === 0) {
    const keywords = [
      "Market Cap",
      "Stock PE",
      "PEG Ratio",
      "ROCE",
      "ROE",
      "Dividend Yield",
      "Face Value",
      "Book Value",
      "Price to Book",
    ];
    const cleanedText = cleaned.replace(/\*\*/g, "");
    for (const key of keywords) {
      const regex = new RegExp(`${key}\\s*:\\s*([^\\n\\r*|]+)`, "i");
      const match = cleanedText.match(regex);
      if (match) {
        stats.push({ name: key, value: match[1].trim() });
      }
    }
  }

  return stats;
}

function extractTradingPlan(text: string) {
  const plan = { entry: "N/A", target: "N/A", stopLoss: "N/A" };
  if (!text) return plan;

  const cleaned = cleanText(text);
  const entryMatch = cleaned.match(
    /(?:Entry Range|Entry Range:|Entry Price|Recommended entry price level):\s*([^\n\r*]+)/i,
  );
  const targetMatch = cleaned.match(
    /(?:Targets|Technical targets|Target Price|Target):\s*([^\n\r*]+)/i,
  );
  const stopLossMatch = cleaned.match(
    /(?:Stop Loss|Recommended Stop Loss level|Stoploss):\s*([^\n\r*]+)/i,
  );

  if (entryMatch) plan.entry = entryMatch[1].trim();
  if (targetMatch) plan.target = targetMatch[1].trim();
  if (stopLossMatch) plan.stopLoss = stopLossMatch[1].trim();

  return plan;
}

function extractVerdict(text: string) {
  const verdict = {
    rating: "HOLD",
    target: "N/A",
    horizon: "N/A",
    riskReward: "N/A",
  };
  if (!text) return verdict;

  const cleaned = cleanText(text);
  const ratingMatch = cleaned.match(
    /(?:Rating|Investment Rating|Final Verdict):\s*\*?\*?(BUY|HOLD|SELL)\*?\*?/i,
  );
  const targetMatch = cleaned.match(
    /(?:Target Price|Fair Value Estimate|Target):\s*\*?\*?([^\n\r*|]+)/i,
  );
  const horizonMatch = cleaned.match(
    /(?:Investment Horizon|Horizon):\s*\*?\*?([^\n\r*|]+)/i,
  );
  const rrMatch = cleaned.match(
    /(?:Risk-Reward Ratio|Risk-Reward|Risk Reward):\s*\*?\*?([^\n\r*|]+)/i,
  );

  if (ratingMatch) verdict.rating = ratingMatch[1].toUpperCase();
  if (targetMatch) verdict.target = targetMatch[1].trim();
  if (horizonMatch) verdict.horizon = horizonMatch[1].trim();
  if (rrMatch) verdict.riskReward = rrMatch[1].trim();

  return verdict;
}

interface ParsedNews {
  date: string;
  title: string;
  summary: string;
  sentiment: "positive" | "negative" | "neutral";
}

function extractNewsItems(text: string): ParsedNews[] {
  const items: ParsedNews[] = [];
  if (!text) return items;

  const cleaned = cleanText(text);

  let newsText = cleaned;
  const index = cleaned.search(
    /(?:Stock-Specific News|News Updates|Company News)/i,
  );
  if (index !== -1) {
    newsText = cleaned.substring(index);
    const nextSection = newsText.indexOf("\n##", 10);
    if (nextSection !== -1) {
      newsText = newsText.substring(0, nextSection);
    }
  }

  const lines = newsText.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (
      trimmed.startsWith("*") ||
      trimmed.startsWith("-") ||
      /^\d+\./.test(trimmed)
    ) {
      const dateMatch = trimmed.match(
        /(?:\[)?(\d{2}[-.\/]\d{2}[-.\/]\d{4})(?:\])?/,
      );
      const date = dateMatch ? dateMatch[1] : "";

      const sentimentMatch = trimmed.match(/\((Positive|Negative|Neutral)\)/i);
      const sentiment = sentimentMatch
        ? (sentimentMatch[1].toLowerCase() as
            | "positive"
            | "negative"
            | "neutral")
        : "neutral";

      const cleanLine = trimmed
        .replace(/^[*-\d.\s]+/, "")
        .replace(/(?:\[)?\d{2}[-.\/]\d{2}[-.\/]\d{4}(?:\])?[:\s]*/, "")
        .replace(/\((Positive|Negative|Neutral)\)/i, "")
        .trim();

      let title = cleanLine;
      let summary = "";

      const splitIndex = cleanLine.search(/[:\-–]/);
      if (splitIndex !== -1) {
        title = cleanLine.substring(0, splitIndex).trim();
        summary = cleanLine.substring(splitIndex + 1).trim();
      }

      title = title.replace(/\*\*/g, "").trim();
      summary = summary.replace(/\*\*/g, "").trim();

      if (title && title.length > 5) {
        items.push({ date, title, summary, sentiment });
      }
    }
  }

  return items;
}

function extractTakeaways(text: string): string[] {
  const takeaways: string[] = [];
  if (!text) return takeaways;

  const cleaned = cleanText(text);
  let tkText = cleaned;
  const index = cleaned.search(
    /(?:Key Takeaways|Takeaways|Investment Thesis Summary)/i,
  );
  if (index !== -1) {
    tkText = cleaned.substring(index);
    const nextSection = tkText.indexOf("\n##", 10);
    if (nextSection !== -1) {
      tkText = tkText.substring(0, nextSection);
    }
  }

  const lines = tkText.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("*") || trimmed.startsWith("-")) {
      const clean = trimmed
        .replace(/^[*-\s]+/, "")
        .replace(/\*\*/g, "")
        .trim();
      if (clean && !clean.toLowerCase().includes("key takeaways")) {
        takeaways.push(clean);
      }
    }
  }

  return takeaways;
}

interface PeerMetric {
  name: string;
  stockVal: string;
  peers: { name: string; val: string }[];
}

function extractPeerMetrics(text: string): {
  peerNames: string[];
  metrics: PeerMetric[];
} {
  const resultData: { peerNames: string[]; metrics: PeerMetric[] } = {
    peerNames: [],
    metrics: [],
  };
  if (!text) return resultData;

  const cleaned = cleanText(text);
  console.log("FULL CLEANED TEXT =", cleaned);
  console.log("PEER RAW TEXT =", cleaned);
  const rows = cleaned.split("\n");
  console.log("PEER RAW TEXT =", cleaned);

  for (const row of rows) {
    if (row.includes("|") && !row.includes("---")) {
      const parts = row
        .split("|")
        .map((p) => p.trim())
        .filter((p) => p !== "");
      if (parts.length >= 2) {
        console.log("ROW =", row);
        console.log("PARTS =", parts);
        if (parts[0].toLowerCase().includes("metric")) {
          resultData.peerNames = parts.slice(2);
        } else {
          const metricName = parts[0].replace(/\*\*/g, "").trim();
          const stockVal = parts[1].trim();
          const peers = parts.slice(2).map((val, idx) => ({
            name: resultData.peerNames[idx] || `Peer ${idx + 1}`,
            val: val.trim(),
          }));

          // if (
          //   metricName &&
          //   stockVal &&
          //   !metricName.toLowerCase().includes("revenue growth")
          // ) 
          const allowedMetrics = [
             "Market Cap",
              "P/E Ratio",
              "ROE"
          ];

if (allowedMetrics.includes(metricName)) {
    resultData.metrics.push({
        name: metricName,
        stockVal,
        peers
    });
}{
          const exists = resultData.metrics.some(
  m => m.name === metricName && m.peers.length > 0
);

if (!exists) {
  resultData.metrics.push({
    name: metricName,
    stockVal,
    peers
  });
} 
  resultData.metrics.push({ name: metricName, stockVal, peers });
            console.log("METRIC PUSH =", {name: metricName, stockVal, peers });
          }
        }
      }
    }
  }
resultData.metrics = resultData.metrics.filter(
  (metric, index, self) =>
    index === self.findIndex(
      m =>
        m.name === metric.name &&
        m.peers.length === metric.peers.length
    )
);
  return resultData;
}

// ============================================================
// SUB-COMPONENTS
// ============================================================

function SentimentGauge({ score }: { score: number }) {
  let pct = 50;
  let label = "NEUTRAL";
  let color = "#FBBC05"; // Yellow
  let desc = "Balanced outlook with mixed indicators.";

  if (score > 10 || score < 0) {
    // scale -100 to 100
    pct = (score + 100) / 2;
    if (score >= 30) {
      label = "BULLISH";
      color = "#34A853"; // Green
      desc = `Strong positive sentiment score of +${score}.`;
    } else if (score <= -30) {
      label = "BEARISH";
      color = "#EA4335"; // Red
      desc = `Caution advised. Negative sentiment score of ${score}.`;
    }
  } else {
    // scale 0 to 10
    pct = score * 10;
    if (score >= 7) {
      label = "BULLISH";
      color = "#34A853";
      desc = `Positive news flow and strong sentiment: ${score}/10.`;
    } else if (score <= 3.5) {
      label = "BEARISH";
      color = "#EA4335";
      desc = `High negativity or caution flags: ${score}/10.`;
    }
  }

  const angle = -90 + (pct / 100) * 180;

  return (
    <div className="flex flex-col items-center p-5 bg-[#151821]/80 rounded-2xl border border-outline-variant/30 shadow-md relative overflow-hidden h-full justify-center">
      <h4 className="text-[10px] text-on-surface-variant uppercase font-mono tracking-widest font-bold mb-3">
        AI Sentiment Meter
      </h4>
      <div className="relative w-48 h-24 flex justify-center items-end">
        <svg className="w-48 h-24 overflow-visible" viewBox="0 0 200 100">
          <defs>
            <linearGradient
              id="gauge-gradient"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
            >
              <stop offset="0%" stopColor="#EA4335" />
              <stop offset="50%" stopColor="#FBBC05" />
              <stop offset="100%" stopColor="#34A853" />
            </linearGradient>
            <filter
              id="needle-glow"
              x="-20%"
              y="-20%"
              width="140%"
              height="140%"
            >
              <feDropShadow
                dx="0"
                dy="1"
                stdDeviation="2"
                floodColor="#ffffff"
                floodOpacity="0.4"
              />
            </filter>
          </defs>
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="#2d313c"
            strokeWidth="12"
            strokeLinecap="round"
          />
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="url(#gauge-gradient)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <circle cx="100" cy="90" r="8" fill="#ffffff" />
          <circle cx="100" cy="90" r="4" fill="#1e2026" />
          <g transform={`rotate(${angle} 100 90)`}>
            <polygon
              points="97,90 103,90 100,20"
              fill="#ffffff"
              filter="url(#needle-glow)"
            />
          </g>
        </svg>
        <div className="absolute bottom-0 text-center">
          <span
            className="text-2xl font-extrabold font-mono tracking-tight"
            style={{ color }}
          >
            {score}
          </span>
          <p
            className="text-[10px] uppercase font-mono tracking-widest font-extrabold mt-0.5"
            style={{ color }}
          >
            {label}
          </p>
        </div>
      </div>
      <p className="text-xs text-on-surface-variant text-center mt-3 font-sans max-w-xs">
        {desc}
      </p>
    </div>
  );
}

function TradingPlanSlider({
  plan,
  ticker,
}: {
  plan: { entry: string; target: string; stopLoss: string };
  ticker: string;
}) {
  const stopLossNum = parsePrice(plan.stopLoss);
  const entryNum = parsePrice(plan.entry);
  const targetNum = parsePrice(plan.target);

  const hasValidValues = stopLossNum > 0 && entryNum > 0 && targetNum > 0;

  return (
    <div className="bg-[#151821]/80 p-5 rounded-2xl border border-outline-variant/30 shadow-md h-full flex flex-col justify-between">
      <div>
        <h4 className="text-[10px] text-on-surface-variant uppercase font-mono tracking-widest font-bold mb-3">
          Trading Targets ({ticker})
        </h4>

        {hasValidValues ? (
          <div className="my-5">
            <div className="relative h-2 bg-[#2d313c] rounded-full my-6">
              {/* Stop Loss (Red) */}
              <div
                className="absolute w-4 h-4 rounded-full bg-danger border border-white -translate-y-1/4 left-[0%]"
                title={`Stop Loss: ₹${stopLossNum}`}
              />
              {/* Entry range highlight (Blue) */}
              <div
                className="absolute h-full bg-google-blue/30 rounded-full"
                style={{ left: "25%", right: "40%" }}
              />
              {/* Entry pointer */}
              <div
                className="absolute w-4 h-4 rounded-full bg-google-blue border border-white -translate-y-1/4 left-[35%]"
                title={`Entry Range: ${plan.entry}`}
              />
              {/* Target (Green) */}
              <div
                className="absolute w-4 h-4 rounded-full bg-success border border-white -translate-y-1/4 left-[100%]"
                title={`Target Price: ₹${targetNum}`}
              />
            </div>

            <div className="flex justify-between items-start text-xs font-mono mt-2">
              <div className="text-left w-1/3">
                <span className="text-danger font-bold text-[10px] tracking-wider block">
                  STOP LOSS
                </span>
                <p className="text-on-surface font-semibold mt-0.5">
                  {plan.stopLoss}
                </p>
              </div>
              <div className="text-center w-1/3">
                <span className="text-google-blue font-bold text-[10px] tracking-wider block">
                  ENTRY ZONE
                </span>
                <p className="text-on-surface font-semibold mt-0.5">
                  {plan.entry}
                </p>
              </div>
              <div className="text-right w-1/3">
                <span className="text-success font-bold text-[10px] tracking-wider block">
                  TARGET
                </span>
                <p className="text-on-surface font-semibold mt-0.5">
                  {plan.target}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2.5 my-3">
            <div className="p-3 bg-danger/5 rounded-xl border border-danger/20 text-center">
              <span className="text-[9px] text-danger font-mono font-bold tracking-wider uppercase block mb-1">
                Stop Loss
              </span>
              <span className="text-xs font-bold text-on-surface">
                {plan.stopLoss}
              </span>
            </div>
            <div className="p-3 bg-google-blue/5 rounded-xl border border-google-blue/20 text-center">
              <span className="text-[9px] text-google-blue font-mono font-bold tracking-wider uppercase block mb-1">
                Entry Range
              </span>
              <span className="text-xs font-bold text-on-surface truncate block">
                {plan.entry}
              </span>
            </div>
            <div className="p-3 bg-success/5 rounded-xl border border-success/20 text-center">
              <span className="text-[9px] text-success font-mono font-bold tracking-wider uppercase block mb-1">
                Target
              </span>
              <span className="text-xs font-bold text-on-surface">
                {plan.target}
              </span>
            </div>
          </div>
        )}
      </div>
      <p className="text-[10px] text-on-surface-variant font-sans leading-relaxed mt-2 border-t border-outline-variant/10 pt-2 flex items-center gap-1">
        <span className="material-symbols-outlined text-xs text-google-yellow">
          warning
        </span>
        Manage stop-loss strictly on a closing basis.
      </p>
    </div>
  );
}

// ============================================================
// MAIN COMPONENT
// ============================================================

interface ResearchReportPanelProps {
  result: unknown;
  onClose: () => void;
}

interface NormalizedSection {
  status: string;
  data: Record<string, unknown>;
  synthesis: string;
  warnings: string[];
  confidence: number;
  data_freshness?: string;
  source_quality?: string;
  retrieval_status?: string;
}

interface NormalizedReport {
  report_id: string;
  ticker: string;
  company_name?: string;
  executive_summary: string;
  fundamental_analysis: string;
  technical_analysis: string;
  sentiment_analysis: string;
  conclusion: string;
  risk_disclaimer: string;
  sentiment_score: number;
  generation_time_ms: number;
  created_at: string;
  intent: string;
  ui_blocks: string[];
  warnings: string[];
  sections: Record<string, NormalizedSection>;
  citations?: { title: string; source: string; published_at: string }[];
  debug?: Record<string, unknown>;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function normalizeSection(value: unknown, fallbackMessage: string): NormalizedSection {
  const section = asRecord(value);
  if (!Object.keys(section).length) return fallbackSection(fallbackMessage);

  return {
    status: asString(section.status, "unavailable"),
    data: asRecord(section.data),
    synthesis: asString(section.synthesis),
    warnings: asStringArray(section.warnings),
    confidence: Number(section.confidence || 0),
    data_freshness: asString(section.data_freshness),
    source_quality: asString(section.source_quality),
    retrieval_status: asString(section.retrieval_status),
  };
}

function fallbackSection(message: string): NormalizedSection {
  return {
    status: "unavailable",
    data: {},
    synthesis: "",
    warnings: [message],
    confidence: 0,
    source_quality: "Unavailable",
    retrieval_status: "missing",
  };
}

function markdownFromSection(section?: NormalizedSection, fallback = "") {
  if (!section) return fallback;
  const data = section.data;
  const parts = [
    section.synthesis,
    asString(data.summary),
    asString(data.financial_health),
    asString(data.competitive_moat),
    asString(data.trend_analysis),
    asString(data.momentum_analysis),
    asString(data.key_levels),
    asString(data.peer_comparison),
    asStringArray(data.key_factors).join("\n"),
    asStringArray(data.key_themes).join("\n"),
    section.confidence ? `Confidence Score: ${section.confidence}%` : "",
  ].filter(Boolean);
  return parts.join("\n\n") || fallback;
}

function normalizeReportPayload(payload: unknown): NormalizedReport {
  const root = asRecord(payload);
  const meta = asRecord(root.meta);
  const payloadSections = asRecord(root.sections);
  const isEnvelope = Boolean(root.meta && root.sections);
  const sections = isEnvelope
    ? {
        fundamentals: normalizeSection(payloadSections.fundamentals, "No fundamental data available."),
        technicals: normalizeSection(payloadSections.technicals, "No technical data available."),
        sentiment: normalizeSection(payloadSections.sentiment, "No sentiment data available."),
        valuation: normalizeSection(payloadSections.valuation, "No valuation data available."),
      }
    : {
        fundamentals: fallbackSection("Legacy response did not include structured fundamentals."),
        technicals: fallbackSection("Legacy response did not include structured technicals."),
        sentiment: fallbackSection("Legacy response did not include structured sentiment."),
        valuation: fallbackSection("Legacy response did not include structured valuation."),
      };

  const finalData = asRecord(root.data);
//       console.log("ROOT =", JSON.stringify(root, null, 2));
// console.log("FINAL DATA =", JSON.stringify(finalData, null, 2));
  const citations = (Array.isArray(root.citations) ? root.citations : []).map((raw) => {
    const cite = asRecord(raw);

    return {
      title: asString(cite.title) || asString(cite.metric) || asString(cite.source_name) || "Source",
      source: asString(cite.source) || asString(cite.source_name) || "Unknown",
      published_at: asString(cite.published_at) || asString(cite.value) || asString(meta.data_freshness),
    };
  });

  const sentimentScore =
    sections.sentiment?.data?.sentiment_score ??
    root.sentiment_score ??
    50;
  const debug = asRecord(root.debug);
  console.log("ROOT COMPANY NAME =", root.company_name);
console.log("FINAL COMPANY NAME =", finalData.company_name);
console.log("COMPANY OVERVIEW =", root.company_overview);
console.log("FUNDAMENTAL ANALYSIS =",root.fundamental_analysis);
const companyMatch = asString(root.fundamental_analysis).match(
    /\*\*Company Analysis:\s*(.*?)\s*\([A-Z]+\)\*\*/
  );

const extractedCompanyName =
  companyMatch?.[1]?.trim();
console.log(
  "EXTRACTED COMPANY =",
  extractedCompanyName
);
console.log("ROOT TICKER =", root.ticker);
console.log("META TICKER =", meta.ticker);
  return {
    report_id: asString(meta.report_id) || asString(root.report_id) || "pending",
    ticker: asString(meta.ticker) || asString(root.ticker) || "NIFTY",
    company_name:
  asString(root.company_name) ||
  asString(finalData.company_name) ||
  (
    {
      TCS: "Tata Consultancy Services",
      INFY: "Infosys Limited",
      WIPRO: "Wipro Limited",
      HDFCBANK: "HDFC Bank Limited",
      RELIANCE: "Reliance Industries Limited",
      TECHM: "Tech Mahindra Limited",
      HCLTECH: "HCL Technologies Limited",
    } as Record<string, string>
  )[asString(meta.ticker) || asString(root.ticker)] ||
  asString(root.ticker) ||
  "Unknown Company",
    // company_name: extractedCompanyName || asString(root.company_name) || asString(finalData.company_name) || asString(root.ticker) || "Unknown Company",
    // company_name: extractedCompanyName || asString(root.company_name) || asString(finalData.company_name) || "Indian Listed Equity",
    // company_name: asString(root.company_name) || asString(finalData.company_name) || asString(root.ticker),
  //   company_name:
  // asString(root.company_name) ||
  // asString(finalData.company_overview)
  //   .split("(")[0]
  //   .trim() ||
  // asString(root.ticker) ||
  // "Unknown Company",
  // company_name:
  // asString(finalData.company_name) ||
  // asString(root.company_overview)
  //   .split('(')[0]
  //   .trim() ||
  // "Unknown Company",
  // company_name:
  // asString(root.company_name) === "Unknown Company"
  //   ? asString(root.ticker)
  //   : asString(root.company_name),

    executive_summary: asString(root.summary) || asString(root.executive_summary) || "Analysis completed with limited verified data.",
    fundamental_analysis: markdownFromSection(sections.fundamentals, asString(root.fundamental_synthesis) || asString(root.fundamental_analysis)),
    technical_analysis: markdownFromSection(sections.technicals, asString(root.technical_synthesis) || asString(root.technical_analysis)),
    sentiment_analysis: markdownFromSection(sections.sentiment, asString(root.sentiment_synthesis) || asString(root.sentiment_analysis)),
    conclusion: [
      ...asStringArray(finalData.investment_thesis || root.investment_thesis),
      ...asStringArray(finalData.risks || root.risk_analysis),
    ].join("\n\n"),
    risk_disclaimer: asString(root.sebi_disclaimer) || asString(root.risk_disclaimer) || "Educational analysis only. This is not personalized investment advice.",
    sentiment_score: Number(sentimentScore) || 50,
    generation_time_ms: Number(meta.generation_time_ms || root.generation_time_ms || 0),
    created_at: asString(meta.created_at) || asString(root.created_at) || new Date().toISOString(),
    intent: asString(asRecord(root.intent).primary_intent) || "GENERALIZED",
    ui_blocks: asStringArray(root.ui_blocks),
    warnings: asStringArray(root.warnings),
    sections,
    citations,
    debug: Object.keys(debug).length ? debug : undefined,
  };
}

function SectionFallback({ section, label }: { section?: NormalizedSection; label: string }) {
  if (section?.status === "available") return null;
  const message = section?.warnings?.[0] || "No data available for this section.";
  return (
    <div className="p-5 rounded-2xl border border-outline-variant/20 bg-surface-container-high/20 text-sm text-on-surface-variant flex gap-3">
      <span className="material-symbols-outlined text-google-yellow text-lg">
        info
      </span>
      <div>
        <div className="text-on-surface font-semibold mb-1">{label}</div>
        <div>{message}</div>
      </div>
    </div>
  );
}
// function generateChecklist(report: any) {
//   const checklist = [];

//   const text = JSON.stringify(report).toLowerCase();

//   if (text.includes("roe") || text.includes("return on equity")) {
//     checklist.push({
//       status: "success",
//       label: "Strong Return on Equity",
//     });
//   }

//   if (text.includes("profit")) {
//     checklist.push({
//       status: "success",
//       label: "Healthy Profitability",
//     });
//   }

//   if (text.includes("debt")) {
//     checklist.push({
//       status: "warning",
//       label: "Debt Levels Need Monitoring",
//     });
//   }

//   if (text.includes("bullish")) {
//     checklist.push({
//       status: "success",
//       label: "Positive Market Sentiment",
//     });
//   }

//   if (text.includes("bearish")) {
//     checklist.push({
//       status: "warning",
//       label: "Negative Market Sentiment",
//     });
//   }

//   return checklist;
// }
function generateChecklist(report: unknown) {
  const checklist = [];

  const text = JSON.stringify(report).toLowerCase();

  // ROE
  const roeMatch = text.match(/roe[^0-9]*([0-9]+(\.[0-9]+)?)/i);
  if (roeMatch) {
    const roe = parseFloat(roeMatch[1]);

    checklist.push({
      status: roe > 20 ? "success" : "warning",
      label:
        roe > 20
          ? `Strong ROE (${roe}%)`
          : `Weak ROE (${roe}%)`,
    });
  }

  // Profitability
  if (text.includes("net profit margin")) {
    checklist.push({
      status: "success",
      label: "Healthy Profit Margins",
    });
  }

  // Debt
  if (text.includes("debt/equity")) {
    checklist.push({
      status: "warning",
      label: "Review Debt/Equity Levels",
    });
  }

  // Sentiment
  if (text.includes("bullish")) {
    checklist.push({
      status: "success",
      label: "Positive Market Sentiment",
    });
  }

  if (text.includes("bearish")) {
    checklist.push({
      status: "warning",
      label: "Negative Market Sentiment",
    });
  }
  console.log("CHECKLIST =", checklist);
 console.log("REPORT =", report);
 

  return checklist;
}
function ResearchReportPanel({ result, onClose }: ResearchReportPanelProps) {
  const report = normalizeReportPayload(result);
  
  console.log("COMPANY NAME =", report.company_name);
  console.log("FULL REPORT =", report);
  console.log("FULL REPORT FUNDAMENTAL =", report.fundamental_analysis);
console.log("FULL REPORT COMPANY =", report.company_name);


  const sectionStatus = asRecord(report.debug?.section_status);
  const cleanedFundamental =
  report.fundamental_analysis?.replace(/^content=/, "");

  const [activeTab, setActiveTab] = useState<
    "overview" | "fundamental" | "technical" | "sentiment" | "peer"
  >("overview");
  const [checkedTakeaways, setCheckedTakeaways] = useState<
    Record<number, boolean>
  >({});

  const stats = extractKeyStats(report.fundamental_analysis);
  const tradingPlan = extractTradingPlan(report.technical_analysis);
  const verdict = extractVerdict(report.fundamental_analysis);
  const newsItems = extractNewsItems(report.sentiment_analysis);
  const takeaways = extractTakeaways(report.conclusion);
  const thesisChecklist = generateChecklist(report);
  const valuationPeerText = [
    report.sections.valuation?.synthesis,
    asString(report.sections.valuation?.data?.peer_comparison),
  ].filter(Boolean).join("\n\n");
  const peerData = extractPeerMetrics(valuationPeerText || report.fundamental_analysis);
  console.log("PEER DATA =", peerData);
  console.log("PEER DATA FINAL =", peerData);
  console.log("ALL METRICS =", peerData.metrics);
console.log(
  "PEER METRICS ONLY",
  peerData.metrics.filter(m => m.peers.length > 0)
);
console.log("FUNDAMENTAL =", report.fundamental_analysis);
  const toggleTakeaway = (index: number) => {
    setCheckedTakeaways((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const getVerdictColor = (rating: string) => {
    if (rating === "BUY") return "text-success bg-success/10 border-success/30";
    if (rating === "SELL") return "text-danger bg-danger/10 border-danger/30";
    return "text-warning bg-warning/10 border-warning/30";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 30 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="glass-card p-6 md:p-8 rounded-3xl border border-outline-variant/30 mt-8 relative overflow-hidden shadow-2xl w-full"
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-google-blue/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-google-yellow/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-outline-variant/30 pb-6 mb-6 gap-4 relative z-10">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-google-blue/10 border border-google-blue/20 flex items-center justify-center font-bold text-lg text-google-blue tracking-wider">
            {report.ticker.substring(0, 4)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-on-surface tracking-tight font-sans">
                {report.ticker}
              </h2>
              <span className="text-[10px] font-mono bg-surface-container-high px-2 py-0.5 rounded text-on-surface-variant font-bold border border-outline-variant/20 uppercase">
                NSE / BSE
              </span>
            </div>
            
            <p className="text-sm text-on-surface-variant mt-0.5">
              {/* {report.company_name || "Indian Listed Equity"} */}
              {
                report.company_name
                ?.replace(/^content="?/, "")
                ?.replace(/\*\*/g, "")
                ?.replace("Company Analysis:", "")
                ?.trim()
                || "Indian Listed Equity"
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6 self-stretch md:self-auto justify-between md:justify-end border-t md:border-t-0 border-outline-variant/10 pt-4 md:pt-0">
          <div className="text-left md:text-right font-mono text-[11px] text-on-surface-variant space-y-0.5">
            <div>
              LATENCY:{" "}
              <span className="text-on-surface font-semibold">
                {(report.generation_time_ms / 1000).toFixed(2)}s
              </span>
            </div>
            <div>
              UPDATED:{" "}
              <span className="text-on-surface font-semibold">
                {new Date(report.created_at).toLocaleDateString("en-IN", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-surface-container-high/50 hover:bg-surface-container-highest border border-outline-variant/30 flex items-center justify-center text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>
      </div>

      {/* <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 relative z-10">
        <SentimentGauge score={report.sentiment_score} />
        <TradingPlanSlider plan={tradingPlan} ticker={report.ticker} />
        <div className="bg-[#151821]/80 p-5 rounded-2xl border border-outline-variant/30 shadow-md h-full flex flex-col justify-between">
          <div>
            <h4 className="text-[10px] text-on-surface-variant uppercase font-mono tracking-widest font-bold mb-3">
              Educational Outlook
            </h4>
            <div className="flex items-center justify-between mb-4">
              <span
                className={`text-lg font-extrabold px-5 py-2 rounded-xl border flex items-center gap-1.5 ${getVerdictColor(verdict.rating)}`}
              >
                <span className="material-symbols-outlined text-xl">
                  {verdict.rating === "BUY"
                    ? "trending_up"
                    : verdict.rating === "SELL"
                      ? "trending_down"
                      : "drag_indicator"}
                </span>
                {verdict.rating}
              </span>
              <div className="text-right font-mono">
                <span className="text-[10px] text-on-surface-variant block">
                  RISK-REWARD
                </span>
                <span className="text-sm font-bold text-on-surface">
                  {verdict.riskReward}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-outline-variant/10 text-xs">
              <div>
                <span className="text-on-surface-variant block font-mono text-[10px]">
                  TIME HORIZON
                </span>
                <span className="text-on-surface font-semibold">
                  {verdict.horizon}
                </span>
              </div>
              <div className="text-right">
                <span className="text-on-surface-variant block font-mono text-[10px]">
                  FAIR VALUE
                </span>
                <span className="text-on-surface font-semibold">
                  {verdict.target}
                </span>
              </div>
            </div>
          </div>
          <p className="text-[10px] text-on-surface-variant font-sans leading-relaxed mt-3 border-t border-outline-variant/10 pt-2">
            Based on consensus valuation, historical margin profiles, and
            current index momentum setup.
          </p>
        </div>
      </div> */}

      <div className="border-b border-outline-variant/20 mb-6 flex overflow-x-auto gap-2 scrollbar-none relative z-10">
        {[
          { id: "overview", label: "📋 Executive Thesis", icon: "assignment" },
          { id: "fundamental", label: "📊 Fundamentals", icon: "analytics" },
          {
            id: "technical",
            label: "📈 Technical Charting",
            icon: "show_chart",
          },
          { id: "sentiment", label: "📰 Sentiment & News", icon: "newspaper" },
          { id: "peer", label: "👥 Peer Valuations", icon: "compare_arrows" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() =>
              setActiveTab(
                tab.id as "overview" | "fundamental" | "technical" | "sentiment" | "peer",
              )
            }
            className={`flex items-center gap-2 px-5 py-3 border-b-2 text-sm font-semibold tracking-wide whitespace-nowrap transition-all cursor-pointer ${
              activeTab === tab.id
                ? "border-google-blue text-google-blue font-bold bg-google-blue/5 rounded-t-xl"
                : "border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/30 rounded-t-xl"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">
              {tab.icon}
            </span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="relative z-10 min-h-64">
        {activeTab === "overview" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-8"
          >
            <div className="lg:col-span-7 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-on-surface mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-google-blue">
                    lightbulb
                  </span>
                  Executive Summary
                </h3>
                <p className="text-on-surface-variant leading-relaxed text-[15px] bg-[#151821]/30 p-5 rounded-2xl border border-outline-variant/10">
                  {cleanText(report.executive_summary)}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-on-surface mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-google-yellow">
                    gavel
                  </span>
                  Risk Warning & Disclaimer
                </h3>
                <div className="p-4 bg-danger/5 border border-danger/20 rounded-2xl flex gap-3 text-xs text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-danger text-lg flex-shrink-0">
                    warning
                  </span>
                  <div>
                    <span className="text-danger font-bold uppercase block mb-1">
                      RETAIL ADVISORY WARNING
                    </span>
                    {report.risk_disclaimer}
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="bg-[#151821]/50 p-5 rounded-2xl border border-outline-variant/20">
                <h3 className="text-sm font-bold text-on-surface mb-4 flex items-center gap-2 uppercase tracking-wider font-mono">
                  <span className="material-symbols-outlined text-google-green text-sm">
                    checklist
                  </span>
                  Thesis Checklist
                </h3>
                {takeaways.length > 0 ? (
                  <div className="space-y-3">
                    {takeaways.map((item, idx) => (
                      <div
                        key={idx}
                        onClick={() => toggleTakeaway(idx)}
                        className="flex items-start gap-3 cursor-pointer group p-2 hover:bg-surface-container-high/30 rounded-lg transition-colors"
                      >
                        <button className="mt-0.5 flex-shrink-0 flex items-center justify-center">
                          <span
                            className={`material-symbols-outlined text-xl transition-all ${checkedTakeaways[idx] ? "text-success symbol-filled" : "text-on-surface-variant"}`}
                          >
                            {checkedTakeaways[idx]
                              ? "check_circle"
                              : "radio_button_unchecked"}
                          </span>
                        </button>
                        <span
                          className={`text-sm text-on-surface-variant leading-relaxed group-hover:text-on-surface transition-colors ${checkedTakeaways[idx] ? "line-through opacity-50" : ""}`}
                        >
                          {item}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  // <p className="text-xs text-on-surface-variant italic">
                    // <div className="space-y-2">
                    //      {thesisChecklist.map((item, index) => (
                    //       <div
                    //        key={index}
                    //        className="flex items-center gap-2 text-sm"
                    //       ><span>
                    //                 {item.status === "success" ? "✅" : "⚠️"}
                    //         </span>

                    //       <span>{item.label}</span>
                    //                  </div>
                    //    ))}
                    //         </div>.
                    <div className="space-y-2">
                       {thesisChecklist.map((item, index) => (
                          <div
                            key={index}
                             className="flex items-center gap-2 text-sm"
                             >
                               <span>
                                   {item.status === "success" ? "✅" : "⚠️"}
                                </span>

                                 <span>{item.label}</span>
                               </div>
                             ))}
                            </div>
                  // </p>
                )}
              </div>
                                   </div>
                       </motion.div>
                        )}

        {activeTab === "fundamental" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {stats.length > 0 && (
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest font-extrabold text-on-surface-variant mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-google-blue text-[18px]">
                    table_rows
                  </span>
                  BSE/NSE Screener Key Metrics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {stats.map((stat, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-[#151821]/80 rounded-xl border border-outline-variant/20 hover:border-google-blue/30 transition-colors"
                    >
                      <span className="text-[10px] text-on-surface-variant font-mono uppercase block mb-1">
                        {stat.name}
                      </span>
                      <span className="text-lg font-bold text-on-surface font-mono">
                        {stat.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="markdown-body bg-[#151821]/30 p-6 md:p-8 rounded-3xl border border-outline-variant/10">
              <SectionFallback section={report.sections.fundamentals} label="Fundamentals" />
              {report.fundamental_analysis ? (
                // <ReactMarkdown remarkPlugins={[remarkGfm]}>
                //   {cleanText(report.fundamental_analysis)}
                // </ReactMarkdown>
               <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {cleanText(cleanedFundamental || "")}
              </ReactMarkdown>
              ) : null}
            </div>
          </motion.div>
        )}

        {activeTab === "technical" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-5 bg-[#151821]/80 rounded-2xl border border-outline-variant/30 text-center">
                <span className="text-[10px] text-on-surface-variant font-mono uppercase tracking-wider block mb-1">
                  Short-term Trend
                </span>
                <span className="text-2xl font-bold text-success flex items-center justify-center gap-1.5 mt-2">
                  <span className="material-symbols-outlined text-2xl symbol-filled">
                    trending_up
                  </span>
                  BULLISH
                </span>
              </div>
              <div className="p-5 bg-[#151821]/80 rounded-2xl border border-outline-variant/30 text-center">
                <span className="text-[10px] text-on-surface-variant font-mono uppercase tracking-wider block mb-1">
                  RSI (14) Reading
                </span>
                <span className="text-2xl font-bold text-on-surface font-mono block mt-2">
                  62.4
                </span>
                <span className="text-[10px] text-google-yellow font-bold uppercase mt-1 inline-block">
                  Neutral Accumulation
                </span>
              </div>
              <div className="p-5 bg-[#151821]/80 rounded-2xl border border-outline-variant/30 text-center">
                <span className="text-[10px] text-on-surface-variant font-mono uppercase tracking-wider block mb-1">
                  MACD Crossover
                </span>
                <span className="text-2xl font-bold text-success flex items-center justify-center gap-1.5 mt-2">
                  <span className="material-symbols-outlined text-xl">
                    done_all
                  </span>
                  BULLISH CROSS
                </span>
              </div>
            </div>

            <div className="markdown-body bg-[#151821]/30 p-6 md:p-8 rounded-3xl border border-outline-variant/10">
              <SectionFallback section={report.sections.technicals} label="Technical Analysis" />
              {report.technical_analysis ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {cleanText(report.technical_analysis)}
                </ReactMarkdown>
              ) : null}
            </div>
          </motion.div>
        )}

        {activeTab === "sentiment" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {newsItems.length > 0 && (
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest font-extrabold text-on-surface-variant mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-google-red text-[18px]">
                    history_edu
                  </span>
                  Timeline of Key News & Sentiment Impact
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {newsItems.map((news, idx) => (
                    <div
                      key={idx}
                      className={`p-5 rounded-2xl border bg-[#151821]/60 flex flex-col justify-between hover:shadow-md transition-shadow ${
                        news.sentiment === "positive"
                          ? "border-success/20 hover:border-success/40"
                          : news.sentiment === "negative"
                            ? "border-danger/20 hover:border-danger/40"
                            : "border-outline-variant/20 hover:border-outline-variant/40"
                      }`}
                    >
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-[10px] font-mono text-on-surface-variant font-bold bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant/10">
                            {news.date || "LAST 30D"}
                          </span>
                          <span
                            className={`text-[10px] font-mono font-extrabold uppercase px-2 py-0.5 rounded border ${
                              news.sentiment === "positive"
                                ? "text-success bg-success/5 border-success/20"
                                : news.sentiment === "negative"
                                  ? "text-danger bg-danger/5 border-danger/20"
                                  : "text-on-surface-variant bg-surface-container-high border-outline-variant/20"
                            }`}
                          >
                            {news.sentiment}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-on-surface leading-snug line-clamp-2">
                          {news.title}
                        </h4>
                      </div>
                      <p className="text-xs text-on-surface-variant leading-relaxed mt-3 pt-2 border-t border-outline-variant/10">
                        {news.summary}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="markdown-body bg-[#151821]/30 p-6 md:p-8 rounded-3xl border border-outline-variant/10">
              <SectionFallback section={report.sections.sentiment} label="Sentiment & News" />
              {report.sentiment_analysis ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {cleanText(report.sentiment_analysis)}
                </ReactMarkdown>
              ) : null}
            </div>
          </motion.div>
        )}

        {activeTab === "peer" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {peerData.metrics.length > 0 && (
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest font-extrabold text-on-surface-variant mb-5 flex items-center gap-2">
                  <span className="material-symbols-outlined text-google-yellow text-[18px]">
                    balance
                  </span>
                  Sector Multiples Relative Analysis
                </h3>
                {/* <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {peerData.metrics.slice(0, 4).map((metric, idx) => { */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* {peerData.metrics.slice(0, 4).map((metric, idx) => { */}
                  {peerData.metrics.filter(metric => metric.peers.length > 0).map((metric, idx) => {

                    
                    const stockValNum = parsePrice(metric.stockVal);
                    const peerVals = metric.peers
                      .map((p) => ({ name: p.name, val: parsePrice(p.val) }))
                      .filter((p) => p.val > 0);
                    const allVals = [
                      stockValNum,
                      ...peerVals.map((p) => p.val),
                    ];
                    const maxVal = Math.max(...allVals, 1);

                    return (
                      <div
                        key={idx}
                        className="p-5 bg-[#151821]/80 rounded-2xl border border-outline-variant/30"
                      >
                        <span className="text-xs font-bold text-on-surface uppercase block mb-3 font-mono">
                          {metric.name}
                        </span>
                        <div className="space-y-3.5">
                          <div>
                            <div className="flex justify-between text-xs font-semibold mb-1">
                              <span className="text-google-blue font-bold">
                                {report.ticker} (Self)
                              </span>
                              <span className="font-mono text-on-surface">
                                {metric.stockVal}
                              </span>
                            </div>
                            <div className="w-full h-2 bg-[#2d313c] rounded-full overflow-hidden">
                              <div
                                className="h-full bg-google-blue rounded-full shadow-[0_0_8px_#4285f4]"
                                style={{
                                  width: `${(stockValNum / maxVal) * 100}%`,
                                }}
                              />
                            </div>
                          </div>

                          {peerVals.map((peer, pIdx) => (
                            <div key={pIdx}>
                              <div className="flex justify-between text-xs mb-1 text-on-surface-variant font-medium">
                                <span>{peer.name}</span>
                                <span className="font-mono">
                                  {metric.peers[pIdx].val}
                                </span>
                              </div>
                              <div className="w-full h-2 bg-[#2d313c]/50 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-on-surface-variant/40 rounded-full"
                                  style={{
                                    width: `${(peer.val / maxVal) * 100}%`,
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* <div className="markdown-body bg-[#151821]/30 p-6 md:p-8 rounded-3xl border border-outline-variant/10">
              <SectionFallback section={report.sections.valuation} label="Peer Valuation" />
           
            </div> */}
          </motion.div>
        )}
      </div>


    </motion.div>
  );
}

// Market Dashboard Component
function MarketDashboard({ isLoading }: { isLoading: boolean }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });

  const indexCards = [
    {
      ticker: "NIFTY 50",
      price: "22,405.60",
      change: 0.84,
      color: "success",
      data: [15, 5, 10, 12, 2, 2, 2, 2],
    },
    {
      ticker: "SENSEX",
      price: "73,886.15",
      change: 0.72,
      color: "success",
      data: [18, 8, 12, 10, 0, 5, 5, 0],
    },
    {
      ticker: "BANKNIFTY",
      price: "47,321.45",
      change: -0.21,
      color: "danger",
      data: [5, 2, 10, 15, 20, 4, 3, 18],
    },
    {
      ticker: "INDIA VIX",
      price: "15.24",
      change: -2.45,
      color: "danger",
      data: [2, 15, 5, 18, 10, 8, 15, 7],
    },
  ];

  return (
    <motion.section
      ref={ref}
      className="w-full px-6 md:px-10 py-16 border-y border-outline-variant/30 bg-surface-container-lowest/50 backdrop-blur-sm overflow-hidden relative"
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="absolute right-0 top-0 w-1/3 h-full bg-gradient-to-l from-google-blue/5 to-transparent pointer-events-none" />

      <div className="max-w-[1400px] mx-auto relative z-10">
        <div className="flex justify-between items-end mb-8">
          <motion.h3
            className="font-title-lg text-2xl text-on-surface flex items-center gap-2 font-bold tracking-tight"
            initial={{ opacity: 0, x: -20 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ duration: 0.6 }}
          >
            <span className="material-symbols-outlined text-google-blue symbol-filled">
              dashboard
            </span>
            Market Dashboard
          </motion.h3>
          <div className="flex items-center gap-4 text-on-surface-variant text-sm font-medium">
            <span className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
              </span>
              {isLoading ? "Loading..." : "Live Updates"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {indexCards.map((card, idx) => (
            <motion.div
              key={card.ticker}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.6, delay: idx * 0.1 }}
            >
              <IndexCard
                ticker={card.ticker}
                price={card.price}
                change={card.change}
                color={card.color as "success" | "danger"}
                data={card.data}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </motion.section>
  );
}

// Hotlist Section Component
function HotlistSection({ hotlistData }: { hotlistData: StockData[] }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });

  return (
    <motion.section
      ref={ref}
      className="w-full px-6 md:px-10 py-24 bg-surface relative overflow-hidden"
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-[1400px] mx-auto grid lg:grid-cols-12 gap-12 relative z-10">
        {/* Multi-Agent Explanation */}
        <motion.div
          className="lg:col-span-4 flex flex-col gap-8"
          initial={{ opacity: 0, x: -30 }}
          animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-google-blue text-sm">
                hub
              </span>
              <span className="text-google-blue font-label-lg text-sm uppercase tracking-widest font-bold">
                Architecture Diagram
              </span>
            </div>
            <h2 className="font-headline-lg text-2xl text-on-surface font-bold tracking-tight">
              Multi-Agent <br />
              Orchestration
            </h2>
            <p className="font-body-md text-body-lg text-on-surface-variant mt-4 leading-relaxed">
              SentiNews does not rely on a single model. We deploy specialized AI
              agents that debate and synthesize data to produce high-conviction
              insights.
            </p>
          </div>

          <div className="flex flex-col gap-6 relative">
            <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-google-blue/50 via-outline-variant/30 to-transparent" />

            {AGENTS.map((agent, idx) => (
              <motion.div
                key={agent.title}
                className="glass-card p-5 rounded-2xl flex gap-5 items-start relative z-10 border-l-4 hover:shadow-lg"
                style={{
                  borderLeftColor: `var(--${agent.color})`,
                }}
                initial={{ opacity: 0, x: -20 }}
                animate={
                  isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }
                }
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                whileHover={{ x: 10 }}
              >
                <div
                  className="p-3 rounded-xl border text-white relative"
                  style={{
                    backgroundColor: `rgba(66, 133, 244, 0.1)`,
                    borderColor: `rgba(66, 133, 244, 0.2)`,
                  }}
                >
                  <span className="material-symbols-outlined">
                    {agent.icon}
                  </span>
                  <span className="absolute -top-1 -right-1 flex h-3 w-3">
                    <span
                      className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                      style={{
                        backgroundColor: `var(--${agent.color})`,
                      }}
                    />
                    <span
                      className="relative inline-flex rounded-full h-3 w-3 border border-surface"
                      style={{
                        backgroundColor: `var(--${agent.color})`,
                      }}
                    />
                  </span>
                </div>

                <div>
                  <h4 className="font-title-lg text-lg text-on-surface mb-1 font-semibold flex justify-between items-center">
                    {agent.title}
                    <span className="text-[10px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface-variant font-mono">
                      {agent.status}
                    </span>
                  </h4>
                  <p className="font-body-md text-on-surface-variant text-sm">
                    {agent.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Hotlist Terminal */}
        <motion.div
          className="lg:col-span-8 flex flex-col"
          initial={{ opacity: 0, x: 30 }}
          animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
          transition={{ duration: 0.6 }}
        >
          <div className="glass-card rounded-2xl border border-outline-variant/50 overflow-hidden flex flex-col h-full shadow-2xl relative">
            {/* Terminal Header */}
            <div className="p-4 border-b border-outline-variant/50 flex justify-between items-center bg-surface-container-lowest/80 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-3 h-3 rounded-full bg-outline-variant/50"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{
                        duration: 2,
                        delay: i * 0.3,
                        repeat: Infinity,
                      }}
                    />
                  ))}
                </div>
                <h3 className="font-mono text-sm text-on-surface flex items-center gap-2 font-semibold">
                  <span className="material-symbols-outlined text-google-blue text-sm symbol-filled">
                    terminal
                  </span>
                  sentinews_engine --hotlist
                </h3>
              </div>
              <motion.button
                className="text-google-blue font-label-lg text-xs flex items-center gap-1 uppercase tracking-wider font-bold"
                whileHover={{ gap: 8 }}
              >
                View Full Screener
                <span className="material-symbols-outlined text-[14px]">
                  chevron_right
                </span>
              </motion.button>
            </div>

            {/* Terminal Content */}
            <div className="overflow-x-auto w-full bg-[#0b0e15]/90 flex-grow font-mono max-h-96">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-outline-variant/30 text-on-surface-variant text-xs uppercase tracking-wider bg-surface-container-highest/20 sticky top-0">
                    <th className="p-4 font-semibold w-64">Asset</th>
                    <th className="p-4 font-semibold w-32">LTP</th>
                    <th className="p-4 font-semibold w-64">
                      AI Sentiment (Real-time)
                    </th>
                    <th className="p-4 font-semibold w-32">Confidence</th>
                    <th className="p-4 font-semibold">Key Catalyst</th>
                  </tr>
                </thead>
                <tbody className="text-sm divide-y divide-outline-variant/20">
                  {hotlistData.map((stock, idx) => (
                    <motion.tr
                      key={stock.symbol}
                      className="terminal-row group hover:bg-surface-container-highest/20 transition-colors"
                      initial={{ opacity: 0 }}
                      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
                      transition={{ duration: 0.4, delay: idx * 0.05 }}
                      whileHover={{ x: 5 }}
                    >
                      <td className="p-4 border-l-2 border-transparent group-hover:border-google-blue transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded bg-surface-container flex items-center justify-center font-bold text-xs text-on-surface border border-outline-variant/30">
                            {stock.symbol.substring(0, 4)}
                          </div>
                          <div>
                            <div className="font-semibold text-on-surface">
                              {stock.symbol}
                            </div>
                            <div className="text-[10px] text-on-surface-variant font-sans">
                              {stock.company}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="text-on-surface">{stock.ltp}</div>
                        <div
                          className={`text-[10px] flex items-center mt-0.5 ${stock.change > 0 ? "text-success" : "text-danger"}`}
                        >
                          <span className="material-symbols-outlined text-[12px]">
                            {stock.change > 0
                              ? "arrow_drop_up"
                              : "arrow_drop_down"}
                          </span>
                          {Math.abs(stock.change)}%
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <motion.div
                            className="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden"
                            whileHover={{ scale: 1.2 }}
                          >
                            <motion.div
                              className={`h-full ${
                                stock.sentiment_type === "bull"
                                  ? "bg-success shadow-[0_0_8px_#34A853]"
                                  : stock.sentiment_type === "bear"
                                    ? "bg-danger shadow-[0_0_8px_#EA4335]"
                                    : "bg-warning shadow-[0_0_8px_#FBBC05]"
                              }`}
                              initial={{ width: 0 }}
                              animate={
                                isInView
                                  ? { width: `${stock.sentiment}%` }
                                  : { width: 0 }
                              }
                              transition={{ duration: 0.8, delay: idx * 0.05 }}
                            />
                          </motion.div>
                          <span
                            className={`text-xs font-semibold ${
                              stock.sentiment_type === "bull"
                                ? "text-success"
                                : stock.sentiment_type === "bear"
                                  ? "text-danger"
                                  : "text-warning"
                            }`}
                          >
                            {stock.sentiment}{" "}
                            {stock.sentiment_type === "bull"
                              ? "[BULL]"
                              : stock.sentiment_type === "bear"
                                ? "[BEAR]"
                                : "[NEUT]"}
                          </span>
                        </div>
                      </td>
                      <td className="p-4 text-xs text-on-surface-variant">
                        <div className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[14px] text-google-blue">
                            verified_user
                          </span>
                          {stock.confidence}%
                        </div>
                      </td>
                      <td
                        className="p-4 text-xs text-on-surface-variant font-sans truncate max-w-[200px]"
                        title={stock.catalyst}
                      >
                        <span className="text-google-blue font-mono mr-2">
                          &gt;
                        </span>
                        {stock.catalyst}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Terminal Footer */}
            <div className="p-3 bg-surface-container-lowest border-t border-outline-variant/30 flex justify-between items-center font-mono text-[10px] text-on-surface-variant">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                SYSTEM: ONLINE
              </div>
              <div className="flex gap-4">
                <span>LATENCY: 42ms</span>
                <span>MODEL: GEMINI-PRO-1.5</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}

// Index Card Component with enhanced animations
interface IndexCardProps {
  ticker: string;
  price: string;
  change: number;
  color: "success" | "danger";
  data: number[];
}

function IndexCard({ ticker, price, change, color, data }: IndexCardProps) {
  const colorClass =
    color === "success"
      ? "text-success bg-success/10 border-success/20"
      : "text-danger bg-danger/10 border-danger/20";

  const svgColor = color === "success" ? "#34A853" : "#EA4335";
  const gradientId = color === "success" ? "grad-success" : "grad-danger";

  return (
    <motion.div
      className="glass-card rounded-2xl p-5 border border-outline-variant/30 cursor-pointer group"
      whileHover={{
        scale: 1.05,
        borderColor: svgColor,
        boxShadow: `0 0 20px ${svgColor}40`,
      }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className="flex justify-between items-start mb-3">
        <span className="font-label-lg text-sm text-on-surface-variant uppercase tracking-wider">
          {ticker}
        </span>
        <motion.span
          className={`font-mono text-xs flex items-center px-2 py-1 rounded-md font-medium border ${colorClass}`}
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <span className="material-symbols-outlined text-[14px]">
            {change > 0 ? "arrow_upward" : "arrow_downward"}
          </span>
          {Math.abs(change)}%
        </motion.span>
      </div>

      <motion.div className="font-headline-md text-xl font-bold text-on-surface mb-2 font-mono tracking-tight">
        {price}
      </motion.div>

      {/* Sparkline */}
      <motion.div className="h-10 w-full relative" whileHover={{ scale: 1.02 }}>
        <svg
          className={`w-full h-full ${colorClass.split(" ")[0]}`}
          style={{
            stroke: svgColor,
            fill: "none",
          }}
          preserveAspectRatio="none"
          viewBox="0 0 100 20"
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" x2="0%" y1="0%" y2="100%">
              <stop offset="0%" stopColor={svgColor} stopOpacity="0.2" />
              <stop offset="100%" stopColor={svgColor} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M0 15 Q 10 5, 20 10 T 40 12 T 60 5 T 80 15 T 100 2"
            fill={`url(#${gradientId})`}
            stroke="none"
          />
          <path
            d="M0 15 Q 10 5, 20 10 T 40 12 T 60 5 T 80 15 T 100 2"
            strokeWidth="2"
          />
        </svg>
      </motion.div>

      {/* Volume indicators */}
      <div className="flex gap-0.5 h-6 mt-1 items-end opacity-50 group-hover:opacity-100 transition-opacity">
        {data.map((value, idx) => (
          <motion.div
            key={idx}
            className={`w-full ${color === "success" ? "bg-success" : "bg-danger"}`}
            style={{
              height: `${(value / 20) * 100}%`,
              opacity: 0.3 + (value / 20) * 0.7,
              borderTopLeftRadius: "2px",
              borderTopRightRadius: "2px",
            }}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: idx * 0.05, type: "spring" }}
            whileHover={{ scaleY: 1.2 }}
          />
        ))}
      </div>
    </motion.div>
  );
}
