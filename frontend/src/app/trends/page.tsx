"use client";
import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { 
  TrendingUp, 
  AlertTriangle, 
  ShieldCheck, 
  Zap, 
  Target, 
  Users, 
  CloudRain, 
  BarChart3,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function TrendsDashboard() {
  const [data, setData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  const [correlations, setCorrelations] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeScale, setTimeScale] = useState<'daily' | 'weekly'>('weekly');

  useEffect(() => {
    async function fetchData() {
      // 1. Fetch trends first for immediate visual feedback
      fetch('http://localhost:8000/api/analytics/trends')
        .then(res => res.json())
        .then(res => {
          setData(res);
          setLoading(false); // Show the charts as soon as we have data!
        })
        .catch(err => console.error("Trends fetch failed", err));

      // 2. Fetch insights in the background (slower AI process)
      fetch('http://localhost:8000/api/analytics/insights')
        .then(res => res.json())
        .then(res => setInsights(res))
        .catch(err => console.error("Insights fetch failed", err));

      // 3. Fetch correlations in the background
      fetch('http://localhost:8000/api/analytics/correlations')
        .then(res => res.json())
        .then(res => setCorrelations(res))
        .catch(err => console.error("Correlations fetch failed", err));
    }
    fetchData();
  }, []);

  const activeTrend = useMemo(() => {
    if (!data) return [];
    return timeScale === 'weekly' ? data.weekly : data.daily;
  }, [data, timeScale]);

  // Helper to shorten the labels for the X-Axis
  const formatXAxis = (tickItem: string) => {
    if (!tickItem) return "";
    // Turn "30th March 2026 - 5th April 2026" into "30 Mar - 05 Apr"
    try {
      const parts = tickItem.split(' - ');
      if (parts.length < 2) return tickItem.substring(0, 10);
      
      const clean = (p: string) => p.replace(/(\d+)(st|nd|rd|th)/, '$1').trim();
      const start = clean(parts[0]);
      const end = clean(parts[1]);
      
      const startD = new Date(start);
      const endD = new Date(end);
      
      if (isNaN(startD.getTime())) return tickItem.split(' ')[0] + '..';

      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      return `${startD.getDate()} ${months[startD.getMonth()]} - ${endD.getDate()} ${months[endD.getMonth()]}`;
    } catch {
      return tickItem.substring(0, 8) + '...';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFCFB] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="font-bold text-vivid-tangerine-900 tracking-widest uppercase text-xs">Synchronizing Intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#FDFCFB] text-slate-900 font-sans pb-20">
      <div className="max-w-7xl mx-auto px-8 pt-12">
        {/* Financial Command Center */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
           <div className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 w-32 h-32 bg-vivid-tangerine-500/5 rounded-full -mr-16 -mt-16 transition-transform group-hover:scale-110"></div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-4">Revenue Accrued</p>
              <h3 className="text-3xl font-black text-slate-900 tracking-tighter">
                KES {(2127050827.72 * (parseFloat(activeTrend[activeTrend.length-1]?.financial_progress) / 100) || 0).toLocaleString()}
              </h3>
              <div className="flex items-center gap-2 mt-4 text-vivid-tangerine-600">
                <Target className="w-3 h-3" />
                <span className="text-[10px] font-bold uppercase tracking-widest">At {activeTrend[activeTrend.length-1]?.financial_progress || '0%'} Progress</span>
              </div>
           </div>
           
           <div className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-4">Slippage Tolerance (10%)</p>
              {(() => {
                const time = parseFloat(activeTrend[activeTrend.length-1]?.time_progress) || 0;
                const work = parseFloat(activeTrend[activeTrend.length-1]?.financial_progress) || 0;
                const lag = time - work;
                return (
                  <>
                    <h3 className={`text-4xl font-black tracking-tighter ${lag > 10 ? 'text-rose-600' : 'text-emerald-600'}`}>
                      {lag > 0 ? '+' : ''}{lag.toFixed(2)}%
                    </h3>
                    <div className={`flex items-center gap-2 mt-4 ${lag > 10 ? 'text-rose-500' : 'text-emerald-500'}`}>
                      <AlertTriangle className="w-3 h-3" />
                      <span className="text-[10px] font-black uppercase tracking-widest">
                        {lag > 10 ? '🔴 CRITICAL PROGRESS DELAY' : '🟢 ON TRACK'}
                      </span>
                    </div>
                  </>
                );
              })()}
           </div>

           <div className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-4">Project Context</p>
              <h3 className="text-xl font-bold text-slate-900 truncate">Makindu Affordable Housing</h3>
              <div className="flex items-center gap-2 mt-4 text-slate-400">
                <Calendar className="w-3 h-3" />
                <span className="text-[10px] font-bold uppercase tracking-widest">KES 2.127B • Week {activeTrend[activeTrend.length-1]?.time_progress ? Math.round((parseFloat(activeTrend[activeTrend.length-1].time_progress) / 100) * 104) : 'N/A'}</span>
              </div>
           </div>
        </div>
      </div>

      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 px-8 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 text-vivid-tangerine-600 hover:text-vivid-tangerine-700 transition-colors">
            <ArrowRight className="rotate-180 w-4 h-4" />
            <span className="font-bold text-sm">Dashboard</span>
          </Link>
          <div className="flex bg-slate-100 p-1 rounded-xl shadow-inner">
            <button 
              onClick={() => setTimeScale('daily')}
              className={`px-6 py-2 rounded-lg text-xs font-bold transition-all ${timeScale === 'daily' ? 'bg-white shadow-sm text-vivid-tangerine-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Daily
            </button>
            <button 
              onClick={() => setTimeScale('weekly')}
              className={`px-6 py-2 rounded-lg text-xs font-bold transition-all ${timeScale === 'weekly' ? 'bg-white shadow-sm text-vivid-tangerine-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Weekly
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-8 pt-12">
        {/* Hero Section */}
        <header className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-vivid-tangerine-100 p-2 rounded-xl">
              <TrendingUp className="text-vivid-tangerine-600 w-6 h-6" />
            </div>
            <h1 className="text-4xl font-black tracking-tight text-slate-900">
              Project Performance <span className="text-vivid-tangerine-600">Analytics</span>
            </h1>
          </div>
          <p className="text-slate-500 max-w-2xl font-medium leading-relaxed">
            Real-time operational intelligence extracted from site reports. Correlating labour momentum, 
            weather conditions, and material logistics.
          </p>
        </header>

        {/* Main Performance Chart */}
        <section className="mb-12">
          <div className="bg-white rounded-[2rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100">
            <div className="flex justify-between items-end mb-10">
              <div>
                <h2 className="text-2xl font-bold mb-2">Labour Force Momentum</h2>
                <p className="text-sm text-slate-400 font-medium italic">Showing {timeScale} personnel trends</p>
              </div>
              <div className="flex gap-8">
                <div className="text-right">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Peak Site Presence</p>
                  <p className="text-2xl font-black text-slate-900">
                    {activeTrend.length > 0 ? Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) : 0}
                  </p>
                </div>
                <div className="text-right border-l border-slate-100 pl-8">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Avg Deployment</p>
                  <p className="text-2xl font-black text-vivid-tangerine-500">
                    {activeTrend.length > 0 ? Math.round(activeTrend.reduce((acc: number, p: any) => acc + (p.value ?? p.labour ?? 0), 0) / activeTrend.length) : 0}
                  </p>
                </div>
              </div>
            </div>

            {/* SVG Chart with Y-Axis */}
            <div className="relative h-96 w-full flex mt-4">
              {/* Y-Axis Labels - Sticky on left */}
              <div className="w-14 h-72 flex flex-col justify-between text-[10px] font-bold text-slate-400 pb-8 pr-3 text-right bg-white z-30 sticky left-0">
                <span>{Math.round((Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) || 100) * 1.1)}</span>
                <span>{Math.round((Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) || 100) / 2)}</span>
                <span>0</span>
              </div>

              {/* Scrollable Chart Viewport */}
              <div className="flex-1 h-80 overflow-x-auto overflow-y-hidden custom-scrollbar pb-12">
                <div 
                  className="h-72 relative flex items-end gap-2 px-4 pb-8 border-b border-l border-slate-100 group/chart transition-all"
                  style={{ minWidth: `${activeTrend.length * (timeScale === 'daily' ? 100 : 150)}px` }}
                >
                {/* Grid Lines */}
                <div className="absolute inset-0 flex flex-col justify-between pb-8 pointer-events-none">
                  <div className="w-full border-t border-slate-50"></div>
                  <div className="w-full border-t border-slate-100/50"></div>
                  <div className="w-full border-t border-slate-50 invisible"></div>
                </div>

                {/* Advanced Momentum Line Overlay */}
                <svg className="absolute inset-0 w-full h-full pb-8 pointer-events-none z-10 overflow-visible" preserveAspectRatio="none">
                   <defs>
                     <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#f97316" stopOpacity="0.1" />
                        <stop offset="50%" stopColor="#f97316" stopOpacity="0.5" />
                        <stop offset="100%" stopColor="#f97316" stopOpacity="0.1" />
                     </linearGradient>
                   </defs>
                   <path 
                    d={activeTrend.map((p: any, i: number) => {
                      const max = (Math.max(...activeTrend.map((pt: any) => pt.value ?? pt.labour ?? 0)) || 1) * 1.1;
                      const val = p.value ?? p.labour ?? 0;
                      const y = 100 - ((val / max) * 100);
                      const pxX = i * (timeScale === 'daily' ? 36 : 100) + 40; 
                      return `${i === 0 ? 'M' : 'L'} ${pxX} ${y * 0.01 * 256}`;
                    }).join(' ')}
                    fill="none"
                    stroke="url(#lineGrad)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                   />
                </svg>

                {activeTrend.map((point: any, i: number) => {
                  const val = point.value ?? point.labour ?? 0;
                  const max = (Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) || 1) * 1.1;
                  const height = (val / max) * 100; 
                  const isDisrupted = point.weather_disrupted;
                  const isWeekend = point.is_weekend;
                  const label = point.label || point.date;
                  
                  return (
                    <div key={i} className={`flex-none ${timeScale === 'daily' ? 'w-8' : 'w-24'} group relative flex flex-col items-center h-full justify-end`}>
                      {/* Bar */}
                      <div 
                        className={`w-full rounded-t-xl transition-all duration-700 relative shadow-md ${isWeekend ? 'bg-slate-200' : isDisrupted ? 'bg-slate-500 shadow-inner' : 'bg-gradient-to-t from-vivid-tangerine-600 to-vivid-tangerine-400'} group-hover:scale-x-110 group-hover:brightness-110 z-20`}
                        style={{ height: `${Math.max(height, 5)}%` }}
                      >
                        {/* Improved Tooltip (Doodle) */}
                        <div className={`absolute ${height > 70 ? 'top-4' : 'bottom-full mb-4'} left-1/2 -translate-x-1/2 bg-slate-900/95 backdrop-blur-md text-white text-[10px] px-4 py-3 rounded-2xl opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100 whitespace-nowrap z-50 pointer-events-none shadow-[0_20px_50px_rgba(0,0,0,0.3)] border border-white/10`}>
                          <div className="flex items-center gap-2 mb-2">
                             <div className={`w-2 h-2 rounded-full ${isDisrupted ? 'bg-slate-400' : 'bg-vivid-tangerine-500'}`}></div>
                             <span className="font-black uppercase tracking-tighter text-[9px]">Executive Site Insight</span>
                          </div>
                          <p className="font-black text-xl text-white mb-0.5">{val} <span className="text-[10px] font-normal text-white/50">Personnel</span></p>
                          <p className="text-white/40 text-[8px] font-bold uppercase mb-2">{label}</p>
                          <div className="flex gap-3 border-t border-white/5 pt-2 mt-1">
                            <div className="flex flex-col">
                               <span className="text-[7px] text-white/30 uppercase">Logistics</span>
                               <span className="text-blue-300 font-bold">📦 {point.materials || 0} Types</span>
                            </div>
                            <div className="flex flex-col border-l border-white/5 pl-3">
                               <span className="text-[7px] text-white/30 uppercase">Condition</span>
                               <span className={isDisrupted ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>{isDisrupted ? '⚠️ Disrupted' : '✅ Optimal'}</span>
                            </div>
                          </div>
                          {/* Arrow (only if tooltip is on top) */}
                          {height <= 70 && <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900"></div>}
                        </div>
                      </div>
                      
                      {/* X-Axis Date */}
                      <span className={`absolute top-full mt-6 text-[10px] font-bold text-slate-400 uppercase tracking-tighter whitespace-nowrap transition-all ${timeScale === 'daily' ? 'rotate-[-45deg] origin-top-left -translate-x-4' : ''}`}>
                        {formatXAxis(label)}
                      </span>
                    </div>
                  );
                })}
                </div>
              </div>
            </div>

            <div className="mt-16 flex gap-6 text-[10px] font-bold uppercase tracking-widest text-slate-400">
                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-vivid-tangerine-500 rounded-sm"></div> Normal Progress</div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-slate-500 rounded-sm"></div> Weather Impacted</div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-slate-200 rounded-sm"></div> Site Closed / Weekend</div>
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-12 mb-12">
          {/* SWOT Analysis */}
          <section className="bg-slate-900 rounded-[2rem] p-10 text-white overflow-hidden relative">
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-8">
                <Target className="text-sunflower-gold-500 w-6 h-6" />
                <h2 className="text-2xl font-bold">SWOT Intelligence</h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                <div className="bg-white/5 p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                  <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest mb-4">Strengths</p>
                  <ul className="space-y-3">
                    {insights?.swot?.strengths?.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-emerald-500 font-bold shrink-0">→</span> {s}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/5 p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                  <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-4">Weaknesses</p>
                  <ul className="space-y-3">
                    {insights?.swot?.weaknesses?.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-rose-500 font-bold shrink-0">→</span> {s}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/5 p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                  <p className="text-[10px] font-black text-sunflower-gold-400 uppercase tracking-widest mb-4">Opportunities</p>
                  <ul className="space-y-3">
                    {insights?.swot?.opportunities?.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-sunflower-gold-500 font-bold shrink-0">→</span> {s}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/5 p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                  <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-4">Threats</p>
                  <ul className="space-y-3">
                    {insights?.swot?.threats?.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-blue-500 font-bold shrink-0">→</span> {s}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Correlations & Scatter Plot */}
          <section className="bg-white rounded-[2rem] p-10 border border-slate-100 shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
             <div className="flex items-center gap-3 mb-8">
                <BarChart3 className="text-vivid-tangerine-500 w-6 h-6" />
                <h2 className="text-2xl font-bold">Operational Correlations</h2>
              </div>
              <p className="text-xs text-slate-400 mb-8 font-medium italic uppercase tracking-wider text-center">Labour Force vs. Logistics Intensity</p>
              
              <div className="h-64 w-full border-l border-b border-slate-100 relative mb-8">
                {correlations?.scatter_labour_materials?.map((d: any, i: number) => {
                  const x = (d.labour / 150) * 100;
                  const y = (d.materials / 15) * 100;
                  return (
                    <div 
                      key={i}
                      className="absolute w-3 h-3 bg-vivid-tangerine-500/30 border border-vivid-tangerine-500 rounded-full cursor-pointer hover:scale-150 transition-transform hover:bg-vivid-tangerine-500 z-10"
                      style={{ left: `${Math.min(95, x)}%`, bottom: `${Math.min(95, y)}%` }}
                    />
                  );
                })}
                <span className="absolute bottom-[-20px] right-0 text-[8px] font-bold text-slate-400">Personnel Count →</span>
                <span className="absolute left-[-40px] top-0 text-[8px] font-bold text-slate-400 rotate-[-90deg] origin-top-right">Material Variety →</span>
              </div>
              <div className="bg-vivid-tangerine-50 p-4 rounded-2xl flex items-center gap-4">
                 <Zap className="text-vivid-tangerine-600 w-5 h-5" />
                 <div>
                   <p className="text-[10px] font-bold text-vivid-tangerine-800 uppercase tracking-widest">Efficiency Insight</p>
                   <p className="text-xs text-vivid-tangerine-600 font-medium">Strong positive correlation detected between steel fixing crew size and reinforcement delivery frequency.</p>
                 </div>
              </div>
          </section>
        </div>

        {/* Stakeholder Recommendations */}
        <section className="bg-white rounded-[2rem] p-12 border border-slate-100 shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
          <div className="flex items-center gap-3 mb-10">
            <Users className="text-vivid-tangerine-600 w-7 h-7" />
            <h2 className="text-2xl font-extrabold">Strategic Recommendations</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-lg">PM</div>
                <h3 className="font-bold text-slate-900">Advice to Project Manager</h3>
              </div>
              <div className="space-y-4">
                {insights?.recommendations?.to_client?.map((r: string, i: number) => (
                  <div key={i} className="flex gap-4 p-5 bg-slate-50 rounded-2xl border border-slate-100 items-start group hover:border-vivid-tangerine-200 transition-colors">
                    <span className="text-vivid-tangerine-500 font-black text-lg">0{i+1}</span>
                    <p className="text-sm text-slate-600 font-medium leading-relaxed">{r}</p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-vivid-tangerine-500 text-white flex items-center justify-center font-bold text-xs shadow-lg">C</div>
                <h3 className="font-bold text-slate-900">Directives to Contractor</h3>
              </div>
              <div className="space-y-4">
                {insights?.recommendations?.to_contractor?.map((r: string, i: number) => (
                  <div key={i} className="flex gap-4 p-5 bg-vivid-tangerine-50/30 rounded-2xl border border-vivid-tangerine-100/50 items-start group hover:border-vivid-tangerine-300 transition-colors">
                    <span className="text-vivid-tangerine-600 font-black text-lg">0{i+1}</span>
                    <p className="text-sm text-slate-600 font-medium leading-relaxed">{r}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Global Verdict Card */}
        <section className="mt-12">
           <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[3rem] p-12 text-white flex flex-col md:flex-row justify-between items-center gap-8 relative overflow-hidden">
             <div className="absolute top-0 right-0 w-96 h-96 bg-vivid-tangerine-500/10 rounded-full blur-3xl -mr-48 -mt-48"></div>
             <div className="relative z-10 max-w-xl">
               <div className="flex items-center gap-3 mb-6">
                 <ShieldCheck className="text-emerald-400 w-8 h-8" />
                 <span className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-400">Claims & Risk Verdict</span>
               </div>
               <h2 className="text-3xl font-bold mb-4">Contractual Exposure Level: <span className={insights?.claim_verdict === 'High' ? 'text-rose-500' : 'text-sunflower-gold-500'}>{insights?.claim_verdict}</span></h2>
               <p className="text-slate-400 text-sm leading-relaxed mb-8">
                 {insights?.executive_summary.substring(0, 200)}...
               </p>
               <button className="px-8 py-3 bg-white text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-transform">
                 Generate Full Audit Report
               </button>
             </div>
             <div className="relative z-10 flex flex-col items-center">
               <div className="w-48 h-48 rounded-full border-8 border-white/5 flex items-center justify-center relative">
                 <div className="absolute inset-4 rounded-full border-8 border-vivid-tangerine-500/20"></div>
                 <div className="text-center">
                   <p className="text-5xl font-black mb-1">{(() => { const time = parseFloat(activeTrend[activeTrend.length-1]?.time_progress) || 0; const work = parseFloat(activeTrend[activeTrend.length-1]?.financial_progress) || 0; const lag = time - work; return Math.max(0, Math.round(lag)); })()}%</p>
                   <p className="text-[8px] font-bold uppercase tracking-widest text-slate-400">Risk Variance</p>
                 </div>
               </div>
             </div>
           </div>
        </section>
      </div>
      
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #e2e2e2;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #d1d1d1;
        }
      `}</style>
    </main>
  );
}
