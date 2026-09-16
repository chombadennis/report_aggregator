"use client";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import NavigationPanel from '@/components/NavigationPanel';
import RevealWrapper from "@/components/animations/RevealWrapper";

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
  EVM: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M3 3v18h18" /><path d="M18 9l-5 5-3-3-5 5" /><circle cx="18" cy="9" r="2" />
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
  <RevealWrapper>
    <div className={`group relative bg-white/90 backdrop-blur border border-vanilla-custard-200 rounded-none p-4 sm:p-7 shadow-sm hover:shadow-xl hover:shadow-vivid-tangerine-100/50 hover:-translate-y-1 transition-all duration-300 overflow-hidden`}>
      <div className={`absolute -top-12 -right-12 w-40 h-40 rounded-full blur-2xl opacity-0 group-hover:opacity-15 transition-opacity duration-500 ${accent}`} />
      <div className="flex items-start gap-4 mb-4">
        <div className={`flex-shrink-0 inline-flex items-center justify-center w-10 h-10 rounded-none ${accent} bg-opacity-10 text-vivid-tangerine-600`}>
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
          <span key={t} className="text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 bg-vanilla-custard-50 text-vivid-tangerine-700 rounded-none border border-vanilla-custard-200">
            {t}
          </span>
        ))}
      </div>
    </div>
  </RevealWrapper>
);

/* ─── Pipeline step ─── */
const Step = ({ num, title, desc }: { num: string; title: string; desc: string }) => (
  <RevealWrapper direction="up">
    <div className="flex gap-5 items-start group">
      <div className="flex-shrink-0 w-10 h-10 rounded-none bg-gradient-to-br from-sunflower-gold-400 to-vivid-tangerine-500 flex items-center justify-center shadow-md shadow-vivid-tangerine-200/50 group-hover:scale-105 transition-transform">
        <span className="text-white font-black text-sm">{num}</span>
      </div>
      <div>
        <h4 className="font-bold text-vivid-tangerine-950 mb-1">{title}</h4>
        <p className="text-sm text-vivid-tangerine-700 leading-relaxed">{desc}</p>
      </div>
    </div>
  </RevealWrapper>
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
  <RevealWrapper direction="up">
    <div className="flex items-center gap-2 px-4 py-2.5 bg-white border border-vanilla-custard-200 rounded-none shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all">
      <span className="text-vivid-tangerine-500">{icon}</span>
      <span className="text-xs font-bold text-vivid-tangerine-800">{label}</span>
    </div>
  </RevealWrapper>
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
      <NavigationPanel />

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
            Field Reporting &amp; Site Analytics Platform
          </div>

          <h1 className="text-3xl md:text-5xl font-bold mb-6 tracking-tight font-serif bg-gradient-to-r from-sunflower-gold-600 via-vivid-tangerine-500 to-vivid-tangerine-700 bg-clip-text text-transparent py-2 leading-[1.15]">
            Vektra
            <br />
            <span className="text-2xl md:text-3xl font-serif font-semibold">Report Aggregator</span>
          </h1>

          <p className="text-base md:text-lg text-vivid-tangerine-800 mb-4 max-w-2xl mx-auto font-medium leading-relaxed">
            A unified smart platform for site reporting, parsing daily logs, generating weekly and monthly reports,
            tracking S-curve production analytics, evaluating project finances, and analysing contractor correspondence,
            EOT claims, and legal documents.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 mb-10">
            {["Daily Logs", "Weekly Reports", "Monthly Reports", "Progress Reports", "EVM", "S-Curve Analytics", "Claims Analysis", "Document Analysis"].map((t) => (
              <span key={t} className="text-[10px] font-black uppercase tracking-wide px-3 py-1.5 bg-vanilla-custard-100 border border-vanilla-custard-200 text-vivid-tangerine-600 rounded-none">
                {t}
              </span>
            ))}
          </div>

          <RevealWrapper direction="up" delay={0.2}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/dashboard" className="group flex items-center gap-2 px-8 py-3.5 bg-vivid-tangerine-600 text-white rounded-none font-bold text-sm shadow-lg shadow-vivid-tangerine-200/50 hover:bg-vivid-tangerine-700 hover:scale-[1.02] transition-all">
                Launch Dashboard
                <span className="group-hover:translate-x-1 transition-transform"><Icon.ChevronRight /></span>
              </Link>
              <Link href="/trends" className="px-8 py-3.5 bg-white/80 backdrop-blur text-vivid-tangerine-700 border border-vanilla-custard-200 rounded-none font-bold text-sm hover:bg-vanilla-custard-50 hover:shadow-md transition-all shadow-sm">
                View Trends
              </Link>
            </div>
          </RevealWrapper>
        </div>

        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-vanilla-custard-50 to-transparent pointer-events-none" />
      </section>

      {/* ── STATS ───────────────────────────────────── */}
      <section className="relative z-10 -mt-1 bg-vanilla-custard-50 py-14">
        <RevealWrapper>
          <div className="max-w-5xl mx-auto px-6">
            <div className="bg-white/90 backdrop-blur-xl rounded-none border border-vanilla-custard-200 shadow-xl py-8 px-4 grid grid-cols-2 md:grid-cols-5 gap-6">
              <Stat value="3" label="Report types" />
              <Stat value="S-Curve" label="Production model" />
              <Stat value="OCR" label="Vision + NLP" />
              <Stat value="Word" label="Export format" />
              <Stat value="Live" label="Financial engine" />
            </div>
          </div>
        </RevealWrapper>
      </section>

      {/* ── CAPABILITIES GRID ───────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Full Platform Capabilities</p>
          <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-3">
            One platform. Every layer of site reporting.
          </h2>
          <p className="text-sm text-vivid-tangerine-700 max-w-xl mx-auto">
            From raw PDF logs to boardroom-ready progress reports — the system covers the full analytical lifecycle of a high-value construction project.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1">
          <CapCard
            icon={<Icon.Scan />}
            label="Parsing Engine"
            title="Vision Log Parsing"
            desc="Automatically extracts structured data from PDF daily site logs using advanced document vision models. Handles scanned pages with a high-resolution rendering fallback at up to 4× zoom for engineering-grade accuracy."
            tags={["Daily Logs", "OCR", "Vision OCR", "Scanned PDFs"]}
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
            desc="Computes cumulative envisaged progress using Hermite smoothstep S-curve interpolation against the baseline project contract value. Calculates daily and weekly revenue earned, recalibrated required velocities, variance (k), and slippage gap for every reporting period."
            tags={["S-Curve", "Contract Value", "Daily Financials", "Weekly Financials", "Monthly Calibration"]}
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
            icon={<Icon.EVM />}
            label="Project Performance"
            title="Earned Value Management (EVM)"
            desc="Monitors project performance against the baseline schedule. It tracks component-level completion and schedule variance to provide quantitative metrics on project health."
            tags={["Component Tracking", "Progress Benchmarking", "Schedule Variance", "Structural Assessment"]}
            accent="bg-sunflower-gold-200"
          />
          <CapCard
            icon={<Icon.ProgressReport />}
            label="Progress Reports"
            title="Project Progress &amp; Site Analysis"
            desc="Generates a full Project Progress &amp; Site Analysis Report in Word format. Includes a recalibration executive summary, monthly production calibration table, weekly recalibration chain, SWOT analysis, strategic recommendations, and a full correspondence register."
            tags={["SWOT Analysis", "Recalibration Chain", "Progress Summary", "Word Export", "Correspondence Register"]}
            accent="bg-vivid-tangerine-200"
          />
          <CapCard
            icon={<Icon.Claim />}
            label="Document Analysis"
            title="Correspondence &amp; Document Analysis"
            desc="Upload any project communication or document. Advanced document analysis models parse each file to extract key requests, action items, and relevant project implications automatically."
            tags={["Documents", "Correspondence", "Site Records", "Auto Analysis", "Action Items"]}
            accent="bg-flag-red-200"
          />
          <CapCard
            icon={<Icon.AI />}
            label="Smart Insights"
            title="Management-Level Executive Summary"
            desc="Feeds the full trend history, financial recalibration data, and uploaded project correspondence into our proprietary analysis engine to produce a management-level executive insight package — including SWOT, stakeholder recommendations, and critical advice summaries."
            tags={["Executive Brief", "Secure Engine", "Recommendations", "Slippage Levels", "SWOT"]}
            accent="bg-vanilla-custard-200"
          />

        </div>
      </section>

      {/* ── DOCUMENT INTELLIGENCE ───────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-14 items-center">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">Document Analysis</p>
              <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950 mb-5">
                Every project document. Fully analysed.
              </h2>
              <p className="text-sm text-vivid-tangerine-700 leading-relaxed mb-8">
                Upload any project communication or document in PDF format. The system automatically classifies the file,
                extracts key action items, and aggregates critical information to help streamline project administration
                and maintain comprehensive correspondence records.
              </p>
              <div className="flex flex-wrap gap-3">
                <DocPill icon={<Icon.Document />} label="Project Documents" />
                <DocPill icon={<Icon.Claim />} label="Official Correspondence" />
                <DocPill icon={<Icon.Shield />} label="Technical Reports" />
                <DocPill icon={<Icon.Contract />} label="Site Records" />
                <DocPill icon={<Icon.Finance />} label="Financial Summaries" />
                <DocPill icon={<Icon.AI />} label="Administrative Records" />
              </div>
            </div>

            {/* Mock document card */}
            <RevealWrapper direction="left">
              <div className="relative">
                <div className="absolute inset-0 rounded-none bg-gradient-to-br from-sunflower-gold-100 to-vanilla-custard-100 opacity-60" />
                <div className="relative rounded-none border border-vanilla-custard-200 overflow-hidden shadow-xl shadow-vanilla-custard-300/30 bg-white/95 backdrop-blur-md p-6 space-y-4 hover:-translate-y-1 transition-transform duration-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400">Project Correspondence</p>
                      <p className="text-sm font-bold text-vivid-tangerine-950 mt-0.5">Communication Log Summary</p>
                    </div>
                    <span className="text-[10px] font-black bg-green-50 text-green-600 border border-green-100 px-2.5 py-1 rounded-none uppercase tracking-wide">Processed</span>
                  </div>
                  <div className="h-px bg-vanilla-custard-100" />
                  {[
                    { label: "Requests Made", val: "Clarification requested regarding site deliverables" },
                    { label: "Action Required", val: "Project team to review milestones and verify progress" },
                    { label: "Contractual Risk", val: "Associated deliverables and key milestones successfully logged" },
                  ].map((r) => (
                    <div key={r.label}>
                      <p className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400 mb-0.5">{r.label}</p>
                      <p className="text-xs text-vivid-tangerine-800 leading-relaxed">{r.val}</p>
                    </div>
                  ))}
                  <div className="flex items-center justify-between pt-2 border-t border-vanilla-custard-100">
                    <span className="text-[10px] font-black uppercase tracking-widest text-vivid-tangerine-400">Analysed by Document Engine</span>
                    <span className="text-[10px] font-bold text-vivid-tangerine-700 bg-vanilla-custard-100 px-3 py-1 rounded-none">May 2026</span>
                  </div>
                </div>
              </div>
            </RevealWrapper>
          </div>
        </div>
      </section>

      {/* ── PIPELINE ────────────────────────────────── */}
      <section className="py-20 max-w-5xl mx-auto px-6">
        <div className="text-center mb-14">
          <p className="text-xs font-black uppercase tracking-widest text-vivid-tangerine-500 mb-2">End-to-End Pipeline</p>
          <h2 className="text-2xl md:text-3xl font-bold font-serif text-vivid-tangerine-950">
            From raw site log to full progress insights
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-10">
          {[
            { n: "1", t: "Upload site logs or project documents", d: "Drop PDF daily logs, progress reports, or project documentation into the dashboard. The system auto-detects the document type." },
            { n: "2", t: "Vision extraction and parsing", d: "Advanced Vision OCR models extract structured data from each page — including labor statistics, material tracking, progress narrative, and key metrics." },
            { n: "3", t: "Aggregation and chronology validation", d: "The aggregation engine compiles logs into weekly and monthly summaries, deduplicates by date, validates chronological alignment, and flags out-of-sequence or mismatched submissions." },
            { n: "4", t: "Financial engine and S-curve calibration", d: "The financial engine computes daily and weekly revenue against the project contract value, calculates S-curve envisaged progress, variance (k), slippage gap, and recalibrated weekly target velocity." },
            { n: "5", t: "Smart insights and strategic recommendations", d: "The advanced analysis engine produces a management executive brief — SWOT analysis, stakeholder insights, and strategic guidance based on project parameters." },
            { n: "6", t: "Generate and download professional reports", d: "Export a fully formatted Weekly Report, Monthly Report, or Project Progress & Site Analysis Report in branded Word format — ready for stakeholder review and sign-off." },
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
            <RevealWrapper direction="right">
              <div className="relative hidden md:block">
                <div className="absolute inset-0 rounded-none bg-gradient-to-br from-sunflower-gold-50 to-vanilla-custard-100 opacity-70" />
                <div className="relative rounded-none border border-vanilla-custard-200 overflow-hidden shadow-xl shadow-vanilla-custard-200/50 bg-white/95 backdrop-blur-md p-6 hover:-translate-y-1 transition-transform duration-500">
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
                          <span className={`text-xs font-black px-2 py-0.5 rounded-none ${row.ok ? "bg-green-50 text-green-700" : "bg-flag-red-50 text-flag-red-600"}`}>{row.k}</span>
                        </div>
                        <div className="h-2 rounded-none bg-vanilla-custard-100 overflow-hidden">
                          <div className="h-full rounded-none bg-gradient-to-r from-sunflower-gold-400 to-vivid-tangerine-500 transition-all duration-700" style={{ width: row.actual }} />
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
            </RevealWrapper>

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
                  "Daily &amp; weekly revenue earned against project contract value",
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
            One click generates a multi-section Project Progress &amp; Site Analysis Report in Word format — pulling from all data sources automatically.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1">
          {[
            { icon: <Icon.Document />, t: "1.0 Executive Summary", d: "Auto-generated management brief reflecting current slippage level, tone-calibrated from constructive to urgent." },
            { icon: <Icon.Finance />, t: "1.1 Recalibration Progress Summary", d: "S-curve mathematical logic, variance explanation, and recalibrated monthly-end targets with weekly velocity requirement." },
            { icon: <Icon.Trend />, t: "2.0 Monthly Production Table", d: "Completed months comparison: actual vs envisaged production and cumulative variance (k) per month." },
            { icon: <Icon.Calendar />, t: "3.0 Weekly Recalibration Chain", d: "Tactical week-by-week variance table showing where momentum was gained or lost throughout the project." },
            { icon: <Icon.Shield />, t: "4.0 SWOT &amp; Progress Insights", d: "Auto-generated SWOT analysis referencing site progress, production recovery, and overall correspondence." },
            { icon: <Icon.AI />, t: "5.0 Strategic Recommendations", d: "Separate actionable recommendations issued to project leads and administrators based on current data." },
            { icon: <Icon.Claim />, t: "6.0 Correspondence Register", d: "Full register of all uploaded documents and correspondence with auto-generated summaries and key implications." },
          ].map((item) => (
            <RevealWrapper key={item.t} direction="up">
              <div className="bg-white/90 backdrop-blur-sm border border-vanilla-custard-200 rounded-none p-4 sm:p-5 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-vivid-tangerine-500">{item.icon}</span>
                  <h4 className="text-sm font-bold text-vivid-tangerine-950">{item.t}</h4>
                </div>
                <p className="text-xs text-vivid-tangerine-700 leading-relaxed">{item.d}</p>
              </div>
            </RevealWrapper>
          ))}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <RevealWrapper>
          <div className="relative rounded-none overflow-hidden bg-gradient-to-br from-sunflower-gold-500 to-vivid-tangerine-600 p-12 text-center shadow-xl shadow-vivid-tangerine-400/30">
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
            <Link href="/dashboard" className="relative z-10 inline-flex items-center gap-2 px-10 py-3.5 bg-white/95 backdrop-blur text-vivid-tangerine-800 rounded-none font-black text-sm shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all">
              Open Dashboard
              <Icon.ChevronRight />
            </Link>
          </div>
        </RevealWrapper>
      </section>

      {/* ── FOOTER ──────────────────────────────────── */}
      <footer className="border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-start gap-8">
          <div>
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Vektra</p>
            <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4">Field Reporting &amp; Analytics</p>
            <div className="flex items-center gap-2.5">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <a href="https://neuralaxislabs.online" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
                <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
              </a>
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
            &copy; 2026 Vektra. All Rights Reserved.
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
