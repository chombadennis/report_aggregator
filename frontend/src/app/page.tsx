"use client";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

/* ─── SVG icon library ───────────────────────────────── */
const Icon = {
  Scan: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" />
      <path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" />
      <rect x="7" y="7" width="10" height="10" rx="1" />
    </svg>
  ),
  Trend: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" />
    </svg>
  ),
  Document: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  Shield: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><polyline points="9 12 11 14 15 10" />
    </svg>
  ),
  Finance: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  ),
  ProgressReport: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  ),
  Claim: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  Correlation: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <circle cx="7" cy="17" r="1.5" /><circle cx="12" cy="11" r="1.5" /><circle cx="17" cy="6" r="1.5" />
      <circle cx="5" cy="10" r="1.5" /><circle cx="14" cy="16" r="1.5" /><circle cx="20" cy="9" r="1.5" />
    </svg>
  ),
  Contract: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M20 14.66V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5.34" />
      <polygon points="18 2 22 6 12 16 8 16 8 12 18 2" />
    </svg>
  ),
  Calendar: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  AI: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
    </svg>
  ),
  ChevronRight: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  ArrowRight: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
      <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
    </svg>
  ),
};

const Orb = ({ className }: { className: string }) => (
  <div className={`absolute rounded-full blur-3xl opacity-20 pointer-events-none ${className}`} />
);

/* ─── Capability card — large grid ─── */
const CapCard = ({
  icon,
  label,
  title,
  desc,
  tags,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  title: string;
  desc: string;
  tags: string[];
  accent: string;
}) => (
  <div className={`group relative bg-white border border-vanilla-custard-100 rounded-2xl sm:rounded-3xl p-4 sm:p-7 shadow-sm hover:shadow-2xl hover:shadow-vivid-tangerine-100 hover:-translate-y-1 transition-all duration-300 overflow-hidden`}>
    <div className={`absolute -top-12 -right-12 w-40 h-40 rounded-full blur-2xl opacity-0 group-hover:opacity-15 transition-opacity duration-500 ${accent}`} />
    <div className="flex items-start gap-4 mb-4">
      <div className={`flex-shrink-0 inline-flex items-center justify-center w-10 h-10 rounded-2xl ${accent} bg-opacity-10 text-vivid-tangerine-600`}>
        {icon}
      </div>
      <div>
        <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400 mb-0.5">{label}</p>
        <h3 className="text-base font-bold text-vivid-tangerine-950">{title}</h3>
      </div>
    </div>
    <p className="text-sm text-vivid-tangerine-700 leading-relaxed mb-4">{desc}</p>
    <div className="flex flex-wrap gap-1.5">
      {tags.map((t) => (
        <span key={t} className="text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 bg-vanilla-custard-100 text-vivid-tangerine-700 rounded-full border border-vanilla-custard-200">
          {t}
        </span>
      ))}
    </div>
  </div>
);

/* ─── Pipeline step ─── */
const Step = ({ num, title, desc }: { num: string; title: string; desc: string }) => (
  <div className="flex gap-5 items-start">
    <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-sunflower-gold-400 to-vivid-tangerine-500 flex items-center justify-center shadow-lg shadow-vivid-tangerine-200">
      <span className="text-white font-black text-sm">{num}</span>
    </div>
    <div>
      <h4 className="font-bold text-vivid-tangerine-950 mb-1">{title}</h4>
      <p className="text-sm text-vivid-tangerine-700 leading-relaxed">{desc}</p>
    </div>
  </div>
);

/* ─── Stat ─── */
const Stat = ({ value, label }: { value: string; label: string }) => (
  <div className="text-center px-4">
    <p className="text-3xl font-bold bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-500 bg-clip-text text-transparent font-serif">{value}</p>
    <p className="text-[10px] font-bold text-vivid-tangerine-600 mt-1 uppercase tracking-widest">{label}</p>
  </div>
);

/* ─── Doc type pill ─── */
const DocPill = ({ icon, label }: { icon: React.ReactNode; label: string }) => (
  <div className="flex items-center gap-2 px-4 py-2.5 bg-white border border-vanilla-custard-200 rounded-2xl shadow-sm">
    <span className="text-vivid-tangerine-500">{icon}</span>
    <span className="text-xs font-bold text-vivid-tangerine-800">{label}</span>
  </div>
);

/* ═══════════════════════════════════════════════════════ */
export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get('error') === 'not-allowed') {
        setShowError(true);
        // Clean up the URL search params so they do not persist on refresh
        const newUrl = window.location.pathname;
        window.history.replaceState({}, '', newUrl);
      }
    }
  }, []);

  useEffect(() => {
    const onScroll = () => {
      if (!heroRef.current) return;
      heroRef.current.style.transform = `translateY(${window.scrollY * 0.22}px)`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-950 font-sans overflow-x-hidden">

      {/* ── NAV ─────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-lg border-b border-vanilla-custard-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-black uppercase tracking-widest text-vivid-tangerine-950">
            MAKS<span className="text-vivid-tangerine-500"> AHP</span>
          </span>
          <div className="flex items-center gap-5">
            <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-900 transition-colors hidden sm:block">Trends</Link>
            <Link href="/contract" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-900 transition-colors hidden sm:block">Contract</Link>
            <Link href="/dashboard" className="px-5 py-2 bg-vivid-tangerine-600 text-white rounded-xl text-xs font-black shadow-md shadow-vivid-tangerine-200 hover:bg-vivid-tangerine-700 hover:scale-[1.03] transition-all">
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-white pt-14">
        <div ref={heroRef} className="absolute inset-0 pointer-events-none will-change-transform">
          <Orb className="w-[620px] h-[620px] bg-sunflower-gold-200 top-[-140px] left-[-180px] animate-pulse" />
          <Orb className="w-[520px] h-[520px] bg-vivid-tangerine-200 bottom-[-100px] right-[-120px] animate-pulse [animation-delay:1.5s]" />
          <Orb className="w-[280px] h-[280px] bg-vanilla-custard-300 top-1/3 left-1/2 -translate-x-1/2 animate-pulse [animation-delay:3s]" />
        </div>
        <div className="absolute inset-0 pointer-events-none opacity-[0.032]"
          style={{ backgroundImage: "linear-gradient(#994f00 1px,transparent 1px),linear-gradient(90deg,#994f00 1px,transparent 1px)", backgroundSize: "40px 40px" }}
        />

        <div className="relative z-10 max-w-4xl mx-auto px-6 py-28 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-vanilla-custard-100 border border-vanilla-custard-200 text-vivid-tangerine-700 text-xs font-bold uppercase tracking-widest mb-8 shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-vivid-tangerine-500 animate-pulse" />
            Field Intelligence &amp; Site Analytics Platform
          </div>

          <h1 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight font-serif bg-gradient-to-r from-sunflower-gold-600 via-vivid-tangerine-500 to-vivid-tangerine-700 bg-clip-text text-transparent py-2 leading-[1.15]">
            Makindu Affordable&nbsp;Housing Project
            <br />
            <span className="text-3xl md:text-4xl font-serif font-semibold">Report Aggregator</span>
          </h1>

          <p className="text-base md:text-lg text-vivid-tangerine-800 mb-4 max-w-2xl mx-auto font-medium leading-relaxed">
            A unified AI-powered platform for site intelligence — parsing daily logs, generating weekly and monthly reports,
            tracking S-curve production analytics, evaluating project finances, and analysing contractor correspondence,
            EOT claims, and legal documents.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 mb-10">
            {["Daily Logs", "Weekly Reports", "Monthly Reports", "Progress Reports", "S-Curve Analytics", "Claims Analysis", "Document Intelligence"].map((t) => (
              <span key={t} className="text-[10px] font-black uppercase tracking-wide px-3 py-1.5 bg-vanilla-custard-100 border border-vanilla-custard-200 text-vivid-tangerine-600 rounded-full">
                {t}
              </span>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/dashboard" className="group flex items-center gap-2 px-8 py-3.5 bg-vivid-tangerine-600 text-white rounded-2xl font-bold text-sm shadow-xl shadow-vivid-tangerine-200 hover:bg-vivid-tangerine-700 hover:scale-[1.03] transition-all">
              Launch Dashboard
              <span className="group-hover:translate-x-1 transition-transform"><Icon.ChevronRight /></span>
            </Link>
            <Link href="/trends" className="px-8 py-3.5 bg-white/80 backdrop-blur text-vivid-tangerine-700 border border-vanilla-custard-200 rounded-2xl font-bold text-sm hover:bg-vanilla-custard-50 transition-all shadow-sm">
              View Trends
            </Link>
          </div>
        </div>

        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-vanilla-custard-50 to-transparent pointer-events-none" />
      </section>

      {/* ── STATS ───────────────────────────────────── */}
      <section className="relative z-10 -mt-1 bg-vanilla-custard-50 py-14">
        <div className="max-w-5xl mx-auto px-6">
          <div className="bg-white/80 backdrop-blur-md rounded-3xl border border-vanilla-custard-100 shadow-lg py-8 px-4 grid grid-cols-2 md:grid-cols-5 gap-6">
            <Stat value="3" label="Report types" />
            <Stat value="S-Curve" label="Production model" />
            <Stat value="AI" label="Vision + NLP" />
            <Stat value="Word" label="Export format" />
            <Stat value="Live" label="Financial engine" />
          </div>
        </div>
      </section>

      {/* ── CAPABILITIES GRID ───────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Full Platform Capabilities</p>
          <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-3">
            One platform. Every layer of site intelligence.
          </h2>
          <p className="text-sm text-vivid-tangerine-700 max-w-xl mx-auto">
            From raw PDF logs to boardroom-ready progress reports — the system covers the full analytical lifecycle of a high-value construction project.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1 md:gap-6">
          <CapCard
            icon={<Icon.Scan />}
            label="Parsing Engine"
            title="AI Vision Log Parsing"
            desc="Automatically extracts structured data from PDF daily site logs using Gemini Vision OCR. Handles scanned pages with a high-resolution rendering fallback at up to 4× zoom for engineering-grade accuracy."
            tags={["Daily Logs", "OCR", "Gemini Vision", "Scanned PDFs"]}
            accent="bg-sunflower-gold-300"
          />
          <CapCard
            icon={<Icon.Calendar />}
            label="Report Generation"
            title="Weekly Report Generation"
            desc="Aggregates 7 parsed daily logs into a structured weekly progress report in branded Word format. Includes labour counts, materials delivered, work progress, and a full executive narrative — generated via live SSE progress streaming."
            tags={["7-Day Aggregation", "Word Export", "Live Progress", "SSE Streaming"]}
            accent="bg-vivid-tangerine-300"
          />
          <CapCard
            icon={<Icon.Document />}
            label="Report Generation"
            title="Monthly Report Generation"
            desc="Compiles multiple weekly reports into a comprehensive monthly summary with chronology validation, month alignment checks, and auto-generated narrative. Detects and flags out-of-sequence submissions before generating."
            tags={["Monthly Rollup", "Chronology Validation", "Narrative", "Word Export"]}
            accent="bg-vanilla-custard-300"
          />
          <CapCard
            icon={<Icon.Finance />}
            label="Financial Engine"
            title="S-Curve Production Analytics"
            desc="Computes cumulative envisaged progress using Hermite smoothstep S-curve interpolation against the KES 2.1B contract sum. Calculates daily and weekly revenue earned, recalibrated required velocities, variance (k), and slippage gap for every reporting period."
            tags={["S-Curve", "KES 2.1B", "Daily Financials", "Weekly Financials", "Monthly Calibration"]}
            accent="bg-deep-space-blue-200"
          />
          <CapCard
            icon={<Icon.Trend />}
            label="Analytics"
            title="Historical Trend Dashboard"
            desc="Builds a unified chronological trend timeline from all daily, weekly, and monthly reports — deduplicating and sorting by actual date. Surfaces labour averages, material deliveries, weather disruption flags, and prose summaries per reporting period."
            tags={["Labour Trends", "Weather Flags", "Material Delivery", "Deduplication"]}
            accent="bg-flag-red-200"
          />
          <CapCard
            icon={<Icon.Correlation />}
            label="Analytics"
            title="Correlation &amp; Scatter Analysis"
            desc="Computes a statistical correlation matrix between average labour turnover, cumulative work progress, and slippage gap. Produces scatter plot datasets for Labour vs. Slippage and Labour vs. Progress visualizations using a custom average labour turnover formula."
            tags={["Correlation Matrix", "Scatter Plots", "Labour Formula", "Heatmaps"]}
            accent="bg-sunflower-gold-200"
          />
          <CapCard
            icon={<Icon.ProgressReport />}
            label="Progress Reports"
            title="Project Progress &amp; Risk Intelligence"
            desc="Generates a full Project Progress &amp; Risk Intelligence Report in Word format. Includes a recalibration executive summary, monthly production calibration table, weekly recalibration chain, SWOT analysis, strategic recommendations to both Client and Contractor, and a full correspondence register."
            tags={["SWOT Analysis", "Recalibration Chain", "Risk Verdict", "Word Export", "Correspondence Register"]}
            accent="bg-vivid-tangerine-200"
          />
          <CapCard
            icon={<Icon.Claim />}
            label="Document Intelligence"
            title="Claims, EOT &amp; Correspondence Analysis"
            desc="Upload any project document — contractor letters, extension of time (EOT) claims, site instructions, payment requests, concrete cube test lab reports, or minutes of meetings. Gemini analyses each document for requests made, action items, and contractual implications, including concrete crush strength evaluation against BS 1881 / KS EAS 18-1 standards."
            tags={["EOT Claims", "Lab Cube Tests", "Contractual Risk", "AI Analysis", "Action Items"]}
            accent="bg-flag-red-200"
          />
          <CapCard
            icon={<Icon.AI />}
            label="AI Insights"
            title="Management-Level AI Executive Summary"
            desc="Feeds the full trend history, financial recalibration data, and uploaded project correspondence into Gemini to produce a management-level executive insight package — including SWOT, stakeholder recommendations, claim risk verdict (Low / Moderate / High), and a critical advice brief."
            tags={["Executive Brief", "Gemini AI", "Claim Verdict", "Slippage Levels", "SWOT"]}
            accent="bg-vanilla-custard-200"
          />
          <CapCard
            icon={<Icon.Contract />}
            label="Contract Intelligence"
            title="Contract Details Extraction"
            desc="Scans the cover pages of any construction progress report to extract and persist permanent contract details — employer, contractor, consultant, contract sum, contract period, date of possession, and scope of works."
            tags={["Contract Sum", "Employer", "Scope of Works", "Auto-Extraction"]}
            accent="bg-deep-space-blue-100"
          />
        </div>
      </section>

      {/* ── DOCUMENT INTELLIGENCE ───────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-14 items-center">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Document Intelligence</p>
              <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-5">
                Every project document. Fully analysed.
              </h2>
              <p className="text-sm text-vivid-tangerine-700 leading-relaxed mb-8">
                Upload any PDF — scanned or digital. The system classifies the document, extracts all requests and action items,
                identifies contractual implications, and flags concrete strength risks using civil engineering standards.
                Every document feeds directly into the Progress Report's correspondence register.
              </p>
              <div className="flex flex-wrap gap-3">
                <DocPill icon={<Icon.Claim />} label="EOT Claims" />
                <DocPill icon={<Icon.Document />} label="Site Instructions" />
                <DocPill icon={<Icon.Finance />} label="Payment Requests" />
                <DocPill icon={<Icon.Shield />} label="Lab Cube Tests" />
                <DocPill icon={<Icon.Document />} label="Minutes of Meetings" />
                <DocPill icon={<Icon.Claim />} label="Contractor Letters" />
                <DocPill icon={<Icon.Contract />} label="Program of Works" />
                <DocPill icon={<Icon.AI />} label="Client Instructions" />
              </div>
            </div>

            {/* Mock document card */}
            <div className="relative">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-sunflower-gold-100 to-vanilla-custard-100 opacity-60" />
              <div className="relative rounded-3xl border border-vanilla-custard-200 overflow-hidden shadow-2xl shadow-vanilla-custard-300/50 bg-white/90 backdrop-blur p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400">EOT Claim — Contractor</p>
                    <p className="text-sm font-bold text-vivid-tangerine-950 mt-0.5">Request for Extension of Time No. 4</p>
                  </div>
                  <span className="text-[10px] font-black bg-flag-red-50 text-flag-red-600 border border-flag-red-100 px-2.5 py-1 rounded-full uppercase tracking-wide">High Risk</span>
                </div>
                <div className="h-px bg-vanilla-custard-100" />
                {[
                  { label: "Requests Made", val: "21-day time extension citing weather disruptions" },
                  { label: "Action Required", val: "PM to review site diary entries and issue formal response" },
                  { label: "Contractual Risk", val: "Potential LD exposure if claim not timeously addressed" },
                ].map((r) => (
                  <div key={r.label}>
                    <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400 mb-0.5">{r.label}</p>
                    <p className="text-xs text-vivid-tangerine-800 leading-relaxed">{r.val}</p>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-2 border-t border-vanilla-custard-100">
                  <span className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400">AI-analysed by Gemini Vision</span>
                  <span className="text-[10px] font-bold text-vivid-tangerine-700 bg-vanilla-custard-100 px-3 py-1 rounded-full">May 2026</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── PIPELINE ────────────────────────────────── */}
      <section className="py-20 max-w-5xl mx-auto px-6">
        <div className="text-center mb-14">
          <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">End-to-End Pipeline</p>
          <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950">
            From raw site log to full progress intelligence
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-10">
          {[
            { n: "1", t: "Upload site logs or project documents", d: "Drop PDF daily logs, weekly reports, contractor letters, EOT claims, or lab test results into the dashboard. The system auto-detects the document type." },
            { n: "2", t: "AI Vision extraction and parsing", d: "Gemini Vision OCR extracts structured data from each page — labour by trade, materials delivered, work progress, weather conditions, requests made, and contractual implications." },
            { n: "3", t: "Aggregation and chronology validation", d: "The aggregation engine compiles logs into weekly and monthly summaries, deduplicates by date, validates chronological alignment, and flags out-of-sequence or mismatched submissions." },
            { n: "4", t: "Financial engine and S-curve calibration", d: "The financial engine computes daily and weekly revenue against the KES 2.1B contract sum, calculates S-curve envisaged progress, variance (k), slippage gap, and recalibrated weekly target velocity." },
            { n: "5", t: "AI insights and risk verdict", d: "Gemini produces a management executive brief — SWOT analysis, stakeholder recommendations, and a Claim Risk Verdict (Low/Moderate/High) based on the slippage gap severity scale." },
            { n: "6", t: "Generate and download professional reports", d: "Export a fully formatted Weekly Report, Monthly Report, or Project Progress & Risk Intelligence Report in branded Word format — ready for stakeholder review and sign-off." },
          ].map((s) => (
            <Step key={s.n} num={s.n} title={s.t} desc={s.d} />
          ))}
        </div>
      </section>

      {/* ── FINANCIAL ENGINE HIGHLIGHT ───────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-14 items-center">
            {/* mock table panel */}
            <div className="relative hidden md:block">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-sunflower-gold-50 to-vanilla-custard-100 opacity-70" />
              <div className="relative rounded-3xl border border-vanilla-custard-200 overflow-hidden shadow-2xl bg-white/90 backdrop-blur p-6">
                <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400 mb-4">Monthly Production Calibration</p>
                <div className="space-y-4">
                  {[
                    { m: "January 2026", actual: "4.21%", env: "3.87%", k: "+0.34%", ok: true },
                    { m: "February 2026", actual: "3.98%", env: "4.19%", k: "-0.21%", ok: false },
                    { m: "March 2026", actual: "3.72%", env: "4.52%", k: "-0.80%", ok: false },
                    { m: "April 2026", actual: "4.10%", env: "4.83%", k: "-0.73%", ok: false },
                  ].map((row) => (
                    <div key={row.m}>
                      <div className="flex justify-between items-center mb-1.5">
                        <span className="text-xs font-bold text-vivid-tangerine-800">{row.m}</span>
                        <span className={`text-xs font-black px-2 py-0.5 rounded-full ${row.ok ? "bg-green-50 text-green-700" : "bg-flag-red-50 text-flag-red-600"}`}>{row.k}</span>
                      </div>
                      <div className="h-2 rounded-full bg-vanilla-custard-100 overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-sunflower-gold-400 to-vivid-tangerine-500 transition-all duration-700" style={{ width: row.actual }} />
                      </div>
                      <div className="flex justify-between mt-0.5">
                        <span className="text-[9px] text-vivid-tangerine-500">Actual: {row.actual}</span>
                        <span className="text-[9px] text-vivid-tangerine-400">Envisaged: {row.env}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 pt-4 border-t border-vanilla-custard-100 flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400">Required velocity</span>
                  <span className="text-sm font-black text-vivid-tangerine-700">1.14% / week</span>
                </div>
              </div>
            </div>

            <div>
              <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Financial Engine</p>
              <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-5">
                Mathematical S-curve recalibration. Week by week.
              </h2>
              <p className="text-sm text-vivid-tangerine-700 leading-relaxed mb-6">
                The financial engine uses Hermite smoothstep polynomial interpolation to model envisaged progress —
                mathematically forgiving the slow mobilisation phase and computing a realistic cumulative deficit
                rather than a penalising linear baseline. Every week, the required catch-up velocity is recalculated
                from scratch against the remaining contract period.
              </p>
              <ul className="space-y-2">
                {[
                  "Daily &amp; weekly revenue earned against KES 2.1B contract sum",
                  "Slippage gap (time elapsed % minus work completed %)",
                  "Variance (k) — actual vs S-curve envisaged per reporting period",
                  "Monthly production calibration: fixed baseline vs rolling recalibration",
                  "Required weekly velocity to recover the timeline",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-vivid-tangerine-700">
                    <span className="mt-1 flex-shrink-0 text-vivid-tangerine-500"><Icon.ArrowRight /></span>
                    <span dangerouslySetInnerHTML={{ __html: item }} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── PROGRESS REPORT HIGHLIGHT ────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Progress Reports</p>
          <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-3">
            What goes into a full progress report?
          </h2>
          <p className="text-sm text-vivid-tangerine-700 max-w-xl mx-auto">
            One click generates a multi-section Project Progress &amp; Risk Intelligence Report in Word format — pulling from all data sources automatically.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1 sm:gap-4">
          {[
            { icon: <Icon.Document />, t: "1.0 Executive Summary", d: "AI-generated management brief reflecting current slippage level, tone-calibrated from constructive to urgent." },
            { icon: <Icon.Finance />, t: "1.1 Recalibration Progress Summary", d: "S-curve mathematical logic, variance explanation, and recalibrated monthly-end targets with weekly velocity requirement." },
            { icon: <Icon.Trend />, t: "2.0 Monthly Production Table", d: "Completed months comparison: actual vs envisaged production and cumulative variance (k) per month." },
            { icon: <Icon.Calendar />, t: "3.0 Weekly Recalibration Chain", d: "Tactical week-by-week variance table showing where momentum was gained or lost throughout the project." },
            { icon: <Icon.Shield />, t: "4.0 SWOT &amp; Risk Intelligence", d: "AI-generated SWOT analysis referencing weather disruptions, site instructions, production recovery, and correspondence." },
            { icon: <Icon.AI />, t: "5.0 Strategic Recommendations", d: "Separate actionable recommendations issued to the Client (PM) and to the Contractor based on current data." },
            { icon: <Icon.Claim />, t: "6.0 Correspondence Register", d: "Full register of all uploaded letters, EOT claims, lab tests, and instructions with AI summaries and contractual implications." },
          ].map((item) => (
            <div key={item.t} className="bg-white border border-vanilla-custard-100 rounded-xl sm:rounded-2xl p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-vivid-tangerine-500">{item.icon}</span>
                <h4 className="text-sm font-bold text-vivid-tangerine-950">{item.t}</h4>
              </div>
              <p className="text-xs text-vivid-tangerine-700 leading-relaxed">{item.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-sunflower-gold-500 to-vivid-tangerine-600 p-12 text-center shadow-2xl shadow-vivid-tangerine-300/50">
          <Orb className="w-80 h-80 bg-white top-[-60px] left-[-60px]" />
          <Orb className="w-80 h-80 bg-white bottom-[-60px] right-[-60px]" />
          <div className="relative z-10 flex items-center justify-center gap-3 mb-4">
            <Icon.Shield />
            <p className="text-white/90 text-xs font-black uppercase tracking-widest">Trusted by the project team</p>
          </div>
          <h2 className="relative z-10 text-2xl md:text-4xl font-bold font-serif text-white mb-4">
            Ready to replace manual reporting?
          </h2>
          <p className="relative z-10 text-white/80 text-sm mb-8 max-w-xl mx-auto leading-relaxed">
            Open the dashboard, upload this week's logs or any project document, and get a professional report — or a full progress report — generated within minutes.
          </p>
          <Link href="/dashboard" className="relative z-10 inline-flex items-center gap-2 px-10 py-3.5 bg-white text-vivid-tangerine-700 rounded-2xl font-black text-sm shadow-lg hover:scale-[1.03] transition-all">
            Open Dashboard
            <Icon.ChevronRight />
          </Link>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────── */}
      <footer className="border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-start gap-8">
          <div>
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
            <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4">Field Intelligence &amp; Reporting</p>
            <div className="flex items-center gap-2.5">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
              <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
            </div>
          </div>
          <div className="flex flex-col items-start md:items-end gap-4">
            <div className="flex gap-5">
              <Link href="/" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Home</Link>
              <Link href="/contract" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Contract</Link>
              <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Trends</Link>
              <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Dashboard</Link>
            </div>
            <div className="flex gap-3">
              <Link href="/terms" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-white border border-vanilla-custard-200 px-3 py-1 rounded-full">Terms</Link>
              <Link href="/privacy" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-white border border-vanilla-custard-200 px-3 py-1 rounded-full">Privacy</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 border-t border-vanilla-custard-100 pt-6 text-center">
          <p className="text-[10px] text-vanilla-custard-400 font-bold uppercase tracking-widest">
            &copy; 2026 Makindu Affordable Housing Project. All Rights Reserved.
          </p>
        </div>
      </footer>

      {showError && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="bg-white/90 backdrop-blur-xl border border-vanilla-custard-200 rounded-3xl p-8 max-w-md w-full text-center shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <button
              onClick={() => setShowError(false)}
              className="absolute top-4 right-4 p-1.5 bg-vanilla-custard-50 hover:bg-vanilla-custard-100 rounded-full border border-vanilla-custard-200 text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-red-100 text-2xl animate-bounce">
              🔒
            </div>
            <h3 className="text-lg font-bold text-red-950 font-serif mb-2">Access Restricted</h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed mb-6 font-medium">
              This account is not allowed to access this reporting portal. Please contact the administrator to request access.
            </p>
            <button
              onClick={() => setShowError(false)}
              className="w-full py-3 bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white rounded-xl text-xs font-black uppercase tracking-wider shadow-lg shadow-vivid-tangerine-500/20 hover:opacity-95 transition-all"
            >
              Acknowledge
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
