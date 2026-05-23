"use client";
import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useAuth, useUser, UserButton } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
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
  ArrowRight,
  Activity,
  Building2,
  TrendingDown,
  Sparkles,
  Loader2
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function TrendsDashboard() {
  const router = useRouter();
  const { isLoaded, userId, getToken, signOut } = useAuth();
  const { user } = useUser();

  const [data, setData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  const [correlations, setCorrelations] = useState<any>(null);
  const [financials, setFinancials] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generatingProgress, setGeneratingProgress] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [downloadingDoc, setDownloadingDoc] = useState(false);
  const [timeScale, setTimeScale] = useState<'daily' | 'weekly'>('weekly');
  const [isMobile, setIsMobile] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [isVerifyingAccess, setIsVerifyingAccess] = useState(() => {
    if (typeof window !== 'undefined') {
      return !sessionStorage.getItem('allowed_user');
    }
    return true;
  });

  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);

  const handleRegenerateInsights = async () => {
    setIsRegenerating(true);
    setRegenerateError(null);
    try {
      const token = await getToken();
      const res = await fetch(`${BACKEND_URL}/api/analytics/insights/regenerate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        throw new Error("Failed to regenerate AI Insights");
      }
      const newInsights = await res.json();
      setInsights(newInsights);
    } catch (err: any) {
      console.error(err);
      setRegenerateError(err.message || "Failed to contact AI Engine");
    } finally {
      setIsRegenerating(false);
    }
  };

  // Client-side Role Checking
  const userEmail = user?.primaryEmailAddress?.emailAddress;
  const adminEmail = process.env.NEXT_PUBLIC_ADMIN_EMAIL || '';
  const isAdmin = userEmail && adminEmail && userEmail.toLowerCase() === adminEmail.toLowerCase();

  // Validate cached user matches current logged-in Clerk user
  useEffect(() => {
    if (isLoaded) {
      if (!userId) {
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('allowed_user');
        }
      } else {
        if (typeof window !== 'undefined') {
          const cached = sessionStorage.getItem('allowed_user');
          if (cached && cached !== userId) {
            sessionStorage.removeItem('allowed_user');
            setIsVerifyingAccess(true);
          }
        }
      }
    }
  }, [isLoaded, userId]);

  // Handle client-side mount
  useEffect(() => {
    setMounted(true);
    if (typeof window !== 'undefined') {
      const handleResize = () => {
        setIsMobile(window.innerWidth < 640);
      };
      handleResize();
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  // Authentication Guard Redirect
  useEffect(() => {
    if (mounted && isLoaded && !userId) {
      router.replace('/login?redirect=/trends');
    }
  }, [mounted, isLoaded, userId, router]);

  useEffect(() => {
    if (!isLoaded || !userId) return;

    async function fetchData() {
      try {
        const token = await getToken();
        const headers = {
          'Authorization': `Bearer ${token}`
        };

        // 1. Fetch trends first for immediate visual feedback
        fetch(`${BACKEND_URL}/api/analytics/trends`, { headers })
          .then(async res => {
            if (res.status === 403) {
              if (typeof window !== 'undefined') {
                sessionStorage.removeItem('allowed_user');
              }
              await signOut({ redirectUrl: '/?error=not-allowed' });
              throw new Error("Access Restricted");
            }
            if (!res.ok) throw new Error("Unauthorized/Error");
            return res.json();
          })
          .then(res => {
            console.log("--- [FRONTEND DEBUG] Trends API response received:", res);
            console.log("Weekly Trends Count:", res?.weekly?.length);
            console.log("Weekly Trends List:", res?.weekly);
            console.log("Daily Trends Count:", res?.daily?.length);
            setData(res);
            if (typeof window !== 'undefined' && userId) {
              sessionStorage.setItem('allowed_user', userId);
            }
            setIsVerifyingAccess(false);
            setLoading(false); // Show the charts as soon as we have data!
          })
          .catch(err => {
            console.error("Trends fetch failed", err);
            setIsVerifyingAccess(false);
            setLoading(false);
          });

        // 2. Fetch insights in the background (slower AI process)
        fetch(`${BACKEND_URL}/api/analytics/insights`, { headers })
          .then(res => {
            if (!res.ok) throw new Error("Unauthorized/Error");
            return res.json();
          })
          .then(res => setInsights(res))
          .catch(err => console.error("Insights fetch failed", err));

        // 3. Fetch correlations in the background
        fetch(`${BACKEND_URL}/api/analytics/correlations`, { headers })
          .then(res => {
            if (!res.ok) throw new Error("Unauthorized/Error");
            return res.json();
          })
          .then(res => setCorrelations(res))
          .catch(err => console.error("Correlations fetch failed", err));

        // 4. Fetch financial trends
        fetch(`${BACKEND_URL}/api/analytics/financials`, { headers })
          .then(res => {
            if (!res.ok) throw new Error("Unauthorized/Error");
            return res.json();
          })
          .then(res => {
            console.log("--- [FRONTEND DEBUG] Financials API response received:", res);
            console.log("Weekly Financials Count:", res?.weekly_financials?.length);
            console.log("Weekly Financials List:", res?.weekly_financials);
            setFinancials(res);
          })
          .catch(err => console.error("Financials fetch failed", err));
      } catch (err) {
        console.error("Failed to fetch analytics", err);
        setIsVerifyingAccess(false);
        setLoading(false);
      }
    }
    fetchData();
  }, [isLoaded, userId, getToken]);

  const activeTrend = useMemo(() => {
    if (!data) return [];
    return timeScale === 'weekly' ? data.weekly : data.daily;
  }, [data, timeScale]);

  const activeFinancials = useMemo(() => {
    if (!financials) return [];
    return timeScale === 'weekly' ? (financials.weekly_financials || []) : (financials.daily_financials || []);
  }, [financials, timeScale]);

  const globalProgress = useMemo(() => {
    if (!data) return { work: 0, time: 0, timeStr: '0%', workStr: '0%' };

    const allRecords = [...(data.weekly || []), ...(data.daily || [])];
    let maxWork = 0;
    let maxWorkStr = '0%';
    let maxTime = 0;
    let maxTimeStr = '0%';

    allRecords.forEach(r => {
      const wVal = r.financial_progress || r.work_completed_percent;
      const w = parseFloat(wVal);
      if (!isNaN(w) && w > maxWork) {
        maxWork = w;
        maxWorkStr = wVal;
      }

      const tVal = r.time_progress || r.time_elapsed_percent;
      const t = parseFloat(tVal);
      if (!isNaN(t) && t > maxTime) {
        maxTime = t;
        maxTimeStr = tVal;
      }
    });

    return { work: maxWork, time: maxTime, workStr: maxWorkStr, timeStr: maxTimeStr };
  }, [data]);

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

  // Dynamically compute the last day of a month (e.g. '31st', '30th', '28th')
  const getMonthLastDay = (monthKey: string): string => {
    try {
      const [monthName, yearStr] = monthKey.split(' ');
      const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
      const monthIdx = months.indexOf(monthName);
      if (monthIdx === -1) return '31st';
      const year = parseInt(yearStr, 10);
      const lastDay = new Date(year, monthIdx + 1, 0).getDate();
      const s = lastDay % 100;
      const suffix = s === 11 || s === 12 || s === 13 ? 'th' : lastDay % 10 === 1 ? 'st' : lastDay % 10 === 2 ? 'nd' : lastDay % 10 === 3 ? 'rd' : 'th';
      return `${lastDay}${suffix}`;
    } catch { return '31st'; }
  };

  const handleGenerateProgress = async () => {
    setGeneratingProgress(true);
    // Simulate generation delay for "UI generation" feel
    setTimeout(() => {
      setGeneratingProgress(false);
      setShowProgressModal(true);
    }, 1500);
  };

  const downloadProgressReport = async () => {
    try {
      setDownloadingDoc(true);
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/generate-progress-report`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Progress_Report_${new Date().toISOString().split('T')[0]}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Progress download error:', error);
      alert('Failed to download report.');
    } finally {
      setDownloadingDoc(false);
    }
  };

  if (!mounted || !isLoaded || isVerifyingAccess) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-16 h-16 border-4 border-vivid-tangerine-50 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">Loading Security Context...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#FDFCFB] text-slate-900 font-sans pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 pt-6 sm:pt-12">
        {/* Financial Command Center */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-8 mb-12">
          <div className="bg-white rounded-[2.5rem] p-5 sm:p-10 border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
            <div className="absolute top-0 right-0 w-32 h-32 bg-vivid-tangerine-500/5 rounded-full -mr-16 -mt-16 transition-transform group-hover:scale-110"></div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-4">Revenue Accrued</p>
            <div className="text-xl font-black text-slate-900 tracking-tight">
              KES {(2127050827.72 * (globalProgress.work / 100) || 0).toLocaleString()}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 italic">Live Ledger</span>
            </div>
          </div>

          <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden flex flex-col group hover:shadow-xl transition-all duration-500 hover:-translate-y-1">
            <div className="p-5 sm:p-8 flex-1">
              <div className="flex justify-between items-start mb-6">
                {(() => {
                  const slippage = globalProgress.time - globalProgress.work;
                  const getStatus = (val: number) => {
                    if (val <= 10) return { label: '🟢 On Track', color: 'emerald', bg: 'bg-emerald-50', text: 'text-emerald-600' };
                    if (val <= 15) return { label: '🟡 Moderate Slippage', color: 'amber', bg: 'bg-amber-50', text: 'text-amber-600' };
                    if (val <= 25) return { label: '🟠 High Slippage', color: 'orange', bg: 'bg-orange-50', text: 'text-orange-600' };
                    return { label: '🔴 Critical Progress Delay', color: 'rose', bg: 'bg-rose-50', text: 'text-rose-600' };
                  };
                  const status = getStatus(slippage);

                  return (
                    <>
                      <div className={`p-3 ${status.bg} rounded-2xl group-hover:scale-110 transition-transform`}>
                        <Activity className={`w-5 h-5 ${status.text}`} />
                      </div>
                      <div className="text-right">
                        <p className={`text-[10px] font-black ${status.text} uppercase tracking-widest mb-1`}>Slippage Gap</p>
                        <p className={`text-2xl font-black tracking-tighter ${status.text}`}>
                          {slippage >= 0 ? '+' : ''}{slippage.toFixed(2)}%
                        </p>
                      </div>
                    </>
                  );
                })()}
              </div>
              {(() => {
                const slippage = globalProgress.time - globalProgress.work;
                const getStatus = (val: number) => {
                  if (val <= 10) return { label: '🟢 On Track', color: 'bg-emerald-500' };
                  if (val <= 15) return { label: '🟡 Moderate Slippage', color: 'bg-amber-500' };
                  if (val <= 25) return { label: '🟠 High Slippage', color: 'bg-orange-500' };
                  return { label: '🔴 Critical Delay', color: 'bg-rose-500' };
                };
                const status = getStatus(slippage);
                return (
                  <div className={`px-4 py-1.5 rounded-full inline-block mb-4 ${status.color} text-white`}>
                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">
                      {status.label}
                    </span>
                  </div>
                );
              })()}
            </div>
            <div className="bg-slate-50 px-8 py-4">
              <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                {(() => {
                  const slippage = globalProgress.time - globalProgress.work;
                  const getColor = (val: number) => {
                    if (val <= 10) return 'bg-emerald-500';
                    if (val <= 15) return 'bg-amber-500';
                    if (val <= 25) return 'bg-orange-500';
                    return 'bg-rose-500';
                  };
                  return (
                    <div
                      className={`h-full transition-all duration-1000 ${getColor(slippage)}`}
                      style={{ width: `${Math.min(100, Math.max(10, slippage * 4))}%` }}
                    ></div>
                  );
                })()}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden flex flex-col group hover:shadow-xl transition-all duration-500 hover:-translate-y-1">
            <div className="p-5 sm:p-8 flex-1 flex flex-col justify-between">
              <div className="flex justify-between items-start mb-6">
                <div className="p-3 bg-blue-50 rounded-2xl group-hover:scale-110 transition-transform">
                  <Building2 className="w-5 h-5 text-blue-500" />
                </div>
                <div className="text-right">
                  <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-1">Project Context</p>
                  <p className="text-lg font-black text-slate-900 leading-none">Makindu Affordable Housing</p>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  KES 2.127B • Week {globalProgress.timeStr !== '0%' ? Math.round((globalProgress.time / 100) * 104) : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 px-3 sm:px-8 py-3 sm:py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-1.5 sm:gap-4">
            <Link href="/" className="text-xs font-bold text-slate-600 uppercase tracking-wider bg-white hover:bg-slate-50 border border-slate-200/80 px-2.5 sm:px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center justify-center">
              Home
            </Link>
            <div className="w-px h-4 bg-slate-200"></div>
            <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-750 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-2.5 sm:px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center gap-1.5">
              <svg className="w-4 h-4 text-vivid-tangerine-500" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </Link>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-4">
            {!isAdmin ? (
              <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50/80 border border-amber-200 px-2 sm:px-3.5 py-1.5 sm:py-2 rounded-xl shadow-sm hidden sm:inline-block">
                Viewer Access
              </span>
            ) : (
              <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50/80 border border-emerald-200 px-2 sm:px-3.5 py-1.5 sm:py-2 rounded-xl shadow-sm hidden sm:inline-block">
                Admin Access
              </span>
            )}
            <UserButton
              afterSignOutUrl="/"
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8 sm:w-9 sm:h-9 border border-vivid-tangerine-200/80 shadow-md hover:scale-105 transition-transform duration-200",
                }
              }}
            />
            <div className="flex bg-slate-100 p-0.5 sm:p-1 rounded-xl shadow-inner">
              <button
                onClick={() => setTimeScale('daily')}
                className={`px-3 sm:px-6 py-1.5 sm:py-2 rounded-lg text-[10px] sm:text-xs font-bold transition-all ${timeScale === 'daily' ? 'bg-white shadow-sm text-vivid-tangerine-600' : 'text-slate-500 hover:text-slate-700'}`}
              >
                Daily
              </button>
              <button
                onClick={() => setTimeScale('weekly')}
                className={`px-3 sm:px-6 py-1.5 sm:py-2 rounded-lg text-[10px] sm:text-xs font-bold transition-all ${timeScale === 'weekly' ? 'bg-white shadow-sm text-vivid-tangerine-600' : 'text-slate-500 hover:text-slate-700'}`}
              >
                Weekly
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-8 pt-6 sm:pt-12">
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

        {/* Financials & Progress Trend Charts */}
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            <div className="bg-white rounded-[2rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100 flex flex-col items-center justify-center h-80">
              <div className="w-10 h-10 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">Analyzing Financial S-Curve...</p>
            </div>
            <div className="bg-white rounded-[2rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100 flex flex-col items-center justify-center h-80">
              <div className="w-10 h-10 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">Calculating Schedule Slippage...</p>
            </div>
          </div>
        ) : financials ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 lg:gap-8 mb-6 lg:mb-12">
            {/* Revenue Trend Line Chart */}
            <section className="bg-white rounded-[2rem] p-4 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100">
              <div className="mb-8">
                <h2 className="text-xl font-bold mb-1">Financial Progress S-Curve</h2>
                <p className="text-xs text-slate-400 font-medium italic">Revenue earned (KES) vs. Time over {timeScale} reporting</p>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeScale === 'weekly' ? financials.weekly_financials : financials.daily_financials}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey={timeScale === 'weekly' ? "label" : "date"}
                      tickFormatter={formatXAxis}
                      tick={{ fontSize: 10, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(value: any) => `K ${(value / 1000000).toFixed(0)}M`}
                      tick={{ fontSize: 10, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                      width={80}
                    />
                    <RechartsTooltip
                      formatter={(value: any) => [`KES ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, "Revenue"]}
                      labelFormatter={(label: any) => `Period: ${label}`}
                      contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}
                    />
                    <Line type="monotone" dataKey="revenue_earned" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#10b981', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Slippage Trend Line Chart */}
            <section className="bg-white rounded-[2rem] p-4 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100">
              <div className="mb-8">
                <h2 className="text-xl font-bold mb-1">Schedule Slippage Gap</h2>
                <p className="text-xs text-slate-400 font-medium italic">% Time Elapsed minus % Work Done over {timeScale} periods</p>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeScale === 'weekly' ? financials.weekly_financials : financials.daily_financials}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey={timeScale === 'weekly' ? "label" : "date"}
                      tickFormatter={formatXAxis}
                      tick={{ fontSize: 10, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(value: any) => `${value}%`}
                      tick={{ fontSize: 10, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                      width={40}
                    />
                    <RechartsTooltip
                      formatter={(value: any) => [`${value}% Gap`, "Slippage"]}
                      labelFormatter={(label: any) => `Period: ${label}`}
                      contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}
                    />
                    <Line type="monotone" dataKey="slippage_gap" stroke="#f43f5e" strokeWidth={3} dot={{ r: 4, fill: '#f43f5e', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
        ) : null}

        {/* Main Performance Chart */}
        {loading ? (
          <section className="mb-12">
            <div className="bg-white rounded-[2rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100 flex flex-col items-center justify-center h-[32rem]">
              <div className="w-12 h-12 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm font-bold text-slate-400 uppercase tracking-widest animate-pulse">Aggregating Labour Force Momentum...</p>
            </div>
          </section>
        ) : (
          <section className="mb-12">
            <div className="bg-white rounded-[2rem] p-4 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.02)] border border-slate-100">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mb-6 sm:mb-10">
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
              <div className={`relative ${isMobile ? 'h-64' : 'h-96'} w-full flex mt-4`}>
                {/* Y-Axis Labels - Sticky on left */}
                <div className={`w-14 ${isMobile ? 'h-48 pb-6' : 'h-72 pb-8'} flex flex-col justify-between text-[10px] font-bold text-slate-400 pr-3 text-right bg-white z-30 sticky left-0`}>
                  <span>{Math.round((Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) || 100) * 1.1)}</span>
                  <span>{Math.round((Math.max(...activeTrend.map((p: any) => p.value ?? p.labour ?? 0)) || 100) / 2)}</span>
                  <span>0</span>
                </div>

                {/* Scrollable Chart Viewport */}
                <div className={`flex-1 ${isMobile ? 'h-56' : 'h-80'} overflow-x-auto overflow-y-visible custom-scrollbar pb-12`}>
                  <div
                    className={`relative flex items-end border-b border-l border-slate-100 group/chart transition-all ${isMobile ? 'h-48 gap-1 px-6 pb-6' : 'h-72 gap-2 px-32 pb-8'}`}
                    style={{
                      minWidth: `${activeTrend.length * (isMobile ? (timeScale === 'daily' ? 32 : 56) : (timeScale === 'daily' ? 48 : 88)) + (isMobile ? 48 : 256)}px`
                    }}
                  >
                    {/* Grid Lines */}
                    <div className={`absolute inset-0 flex flex-col justify-between ${isMobile ? 'pb-6' : 'pb-8'} pointer-events-none`}>
                      <div className="w-full border-t border-slate-50"></div>
                      <div className="w-full border-t border-slate-100/50"></div>
                      <div className="w-full border-t border-slate-50 invisible"></div>
                    </div>

                    {/* Advanced Momentum Line Overlay */}
                    <svg className={`absolute inset-0 w-full h-full ${isMobile ? 'pb-6' : 'pb-8'} pointer-events-none z-10 overflow-visible`} preserveAspectRatio="none">
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
                          
                          const W = isMobile 
                            ? (timeScale === 'daily' ? 24 : 40)
                            : (timeScale === 'daily' ? 40 : 80);
                          const G = isMobile ? 4 : 8;
                          const P = isMobile ? 24 : 128;
                          const pxX = i * (W + G) + P + W / 2;
                          const chartHeight = isMobile ? 168 : 256;
                          
                          return `${i === 0 ? 'M' : 'L'} ${pxX} ${y * 0.01 * chartHeight}`;
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
                        <div key={i} className={`flex-none ${isMobile ? (timeScale === 'daily' ? 'w-6' : 'w-10') : (timeScale === 'daily' ? 'w-10' : 'w-20')} group relative flex flex-col items-center h-full justify-end hover:z-[60]`}>
                          {/* Bar */}
                          <div
                            className={`w-full rounded-t-xl transition-all duration-700 relative shadow-md ${isWeekend ? 'bg-slate-200' : isDisrupted ? 'bg-slate-500 shadow-inner' : 'bg-gradient-to-t from-vivid-tangerine-600 to-vivid-tangerine-400'} group-hover:scale-x-110 group-hover:brightness-110 z-20`}
                            style={{ height: `${Math.max(height, 5)}%` }}
                          >
                            {/* Improved Tooltip (Doodle) - Responsive & Compact on Mobile */}
                            <div className={`absolute bottom-4 
                            ${i < 2 ? 'left-0 translate-x-0' : i > activeTrend.length - 3 ? 'right-0 translate-x-0' : 'left-1/2 -translate-x-1/2'} 
                            bg-slate-900/95 backdrop-blur-md text-white text-[10px] px-3.5 sm:px-5 py-3 sm:py-4 rounded-[1.5rem] opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100 w-52 sm:w-64 z-50 pointer-events-none shadow-[0_20px_60px_rgba(0,0,0,0.4)] border border-white/10`}>

                              <div className="flex justify-between items-center mb-2 sm:mb-3">
                                <div className="flex items-center gap-1.5 sm:gap-2">
                                  <div className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${isDisrupted ? 'bg-slate-400' : 'bg-vivid-tangerine-500'}`}></div>
                                  <span className="font-black uppercase tracking-widest text-[7px] sm:text-[8px] text-white/60">Intelligence Report</span>
                                </div>
                                <span className="text-[7px] sm:text-[8px] font-bold text-white/30 uppercase">{label}</span>
                              </div>

                              <div className="flex justify-between items-end mb-3 sm:mb-4">
                                <div>
                                  <p className="text-[6px] sm:text-[7px] text-white/40 uppercase mb-0.5">Peak Momentum</p>
                                  <p className="font-black text-2xl sm:text-3xl text-white leading-none">{val}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-[6px] sm:text-[7px] text-white/40 uppercase mb-0.5">Site Condition</p>
                                  <span className={`text-[8px] sm:text-[9px] font-black uppercase tracking-widest ${isDisrupted ? 'text-amber-400' : 'text-emerald-400'}`}>
                                    {isDisrupted ? '⚠️ Disrupted' : '✅ Optimal'}
                                  </span>
                                </div>
                              </div>

                              <div className="bg-white/5 rounded-2xl p-2 sm:p-3 mb-2 sm:mb-3 border border-white/5">
                                <div className="flex items-center gap-1.5 sm:gap-2 mb-1.5 sm:mb-2">
                                  <div className="p-0.5 sm:p-1 bg-blue-500/20 rounded-md">
                                    <Layers className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-blue-400" />
                                  </div>
                                  <span className="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-blue-300">Material Logistics</span>
                                </div>
                                <p className="text-[8px] sm:text-[9px] text-white/80 leading-relaxed font-medium line-clamp-2 sm:line-clamp-none">
                                  {typeof point.materials === 'string' ? point.materials : `📦 ${point.materials} categories delivered this period.`}
                                </p>
                              </div>

                              {/* Executive Commentary */}
                              {point.prose_summary && (
                                <div className="space-y-1 hidden sm:block">
                                  <span className="text-[7px] text-white/30 uppercase tracking-widest">Executive Verdict</span>
                                  <p className="text-[8px] text-white/50 leading-relaxed italic line-clamp-3">
                                    "{point.prose_summary.substring(0, 100)}..."
                                  </p>
                                </div>
                              )}

                              {/* Arrow Alignment - Points Down to Bar Bottom */}
                              <div className={`absolute top-full 
                                ${i < 2 ? 'left-6' : i > activeTrend.length - 3 ? 'right-6' : 'left-1/2 -translate-x-1/2'} 
                                border-8 border-transparent border-t-slate-900`}></div>
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
        )}

        <div className="flex flex-col gap-12 mb-12">
          {/* SWOT Analysis */}
          <section className="bg-slate-900 rounded-[2rem] p-5 sm:p-10 text-white overflow-hidden relative">
            <div className="relative z-10">
              <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <Target className="text-sunflower-gold-500 w-6 h-6" />
                  <h2 className="text-2xl font-bold">SWOT Analysis</h2>
                </div>

                {isAdmin && (
                  <button
                    onClick={handleRegenerateInsights}
                    disabled={isRegenerating}
                    className="relative group overflow-hidden bg-gradient-to-r from-sunflower-gold-500 to-amber-500 hover:from-sunflower-gold-600 hover:to-amber-600 text-slate-900 font-black px-5 py-3 rounded-2xl transition-all duration-300 transform active:scale-95 flex items-center gap-2.5 shadow-[0_10px_30px_-10px_rgba(245,158,11,0.5)] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-out" />
                    {isRegenerating ? (
                      <Loader2 className="w-4 h-4 animate-spin text-slate-900" />
                    ) : (
                      <Sparkles className="w-4 h-4 text-slate-900" />
                    )}
                    <span className="tracking-wide text-[10px] uppercase">
                      {isRegenerating ? "Generating..." : "Update AI SWOT Insights"}
                    </span>
                  </button>
                )}
              </div>

              {insights?._generated_at && (
                <div className="text-[10px] font-bold text-slate-400 tracking-wider mb-6 uppercase flex items-center gap-2">
                  <span className="inline-block w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
                  <span>Last Analyzed by AI Engine: {insights._generated_at}</span>
                </div>
              )}

              {regenerateError && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs px-4 py-3 rounded-2xl mb-6">
                  ⚠️ {regenerateError}
                </div>
              )}

              {(!insights || insights.is_empty || (insights.swot?.strengths?.length === 0 && insights.swot?.weaknesses?.length === 0)) ? (
                <div className="bg-white/5 border border-white/10 rounded-3xl p-12 text-center flex flex-col items-center justify-center relative overflow-hidden backdrop-blur-md">
                  <div className="absolute -right-20 -top-20 w-60 h-60 bg-sunflower-gold-500/10 rounded-full blur-[100px] pointer-events-none" />
                  <div className="absolute -left-20 -bottom-20 w-60 h-60 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

                  <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 shadow-2xl">
                    <Sparkles className="w-6 h-6 text-sunflower-gold-400 animate-pulse" />
                  </div>

                  <h3 className="text-lg font-bold mb-2 text-white">AI Strategy Engine Uninitialized</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed mb-6">
                    {isAdmin
                      ? "No AI SWOT analysis or strategic recommendations have been generated for these trends yet. Feed current contract data, financial progress, and site correspondence to AI Engine to generate insights."
                      : "The AI-driven SWOT analysis and strategic recommendations are awaiting administrator generation. Please check back shortly once the administrator compiles the project report."}
                  </p>

                  {isAdmin && (
                    <button
                      onClick={handleRegenerateInsights}
                      disabled={isRegenerating}
                      className="bg-gradient-to-r from-sunflower-gold-500 to-amber-500 hover:from-sunflower-gold-600 hover:to-amber-600 text-slate-900 font-black px-6 py-3 rounded-2xl transition-all transform active:scale-95 flex items-center gap-2.5 shadow-[0_15px_30px_-10px_rgba(245,158,11,0.5)] disabled:opacity-50"
                    >
                      {isRegenerating ? (
                        <Loader2 className="w-4 h-4 animate-spin text-slate-900" />
                      ) : (
                        <Sparkles className="w-4 h-4 text-slate-900" />
                      )}
                      <span className="tracking-widest text-[10px] uppercase">
                        {isRegenerating ? "Running Analysis..." : "Compile AI Insights Now"}
                      </span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-8">
                  <div className="bg-white/5 p-4 sm:p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                    <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest mb-4">Strengths</p>
                    <ul className="space-y-3">
                      {insights?.swot?.strengths?.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-emerald-500 font-bold shrink-0">→</span> {s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-white/5 p-4 sm:p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                    <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-4">Weaknesses</p>
                    <ul className="space-y-3">
                      {insights?.swot?.weaknesses?.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-rose-500 font-bold shrink-0">→</span> {s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-white/5 p-4 sm:p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                    <p className="text-[10px] font-black text-sunflower-gold-400 uppercase tracking-widest mb-4">Opportunities</p>
                    <ul className="space-y-3">
                      {insights?.swot?.opportunities?.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-sunflower-gold-500 font-bold shrink-0">→</span> {s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-white/5 p-4 sm:p-8 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                    <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-4">Threats</p>
                    <ul className="space-y-3">
                      {insights?.swot?.threats?.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex gap-3 leading-relaxed"><span className="text-blue-500 font-bold shrink-0">→</span> {s}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Production Velocity & Recalibration */}
          <section className="bg-white rounded-[2rem] p-4 sm:p-10 border border-slate-100 shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
            <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <Zap className="text-sunflower-gold-600 w-6 h-6" />
                <h2 className="text-2xl font-bold">Production Velocity & Recalibration</h2>
              </div>
              {!isAdmin && (
                <div className="bg-amber-50 border border-amber-100 px-4 py-2.5 rounded-2xl flex items-center gap-2.5 text-xs text-amber-700 font-bold uppercase tracking-wider">
                  <span>🔒</span>
                  <span>Read-Only View: S-Curve Recalibration Locked</span>
                </div>
              )}
            </div>

            {(() => {
              if (!financials || !financials.monthly_financials || financials.monthly_financials.length === 0)
                return <p className="text-slate-400 text-sm italic">Initializing monthly calibration data...</p>;

              const completedMonth = financials.monthly_financials.filter((m: any) => !m.is_ongoing).slice(-1)[0];
              const ongoingMonth = financials.monthly_financials.find((m: any) => m.is_ongoing);
              const latestWeek = (financials.weekly_financials || []).slice(-1)[0];
              const variance = latestWeek?.variance || 0;

              return (
                <div className="space-y-10">
                  {/* Last Completed Month Analysis */}
                  {completedMonth && (
                    <div>
                      <div className="flex items-center gap-2 mb-6">
                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                        <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest">Last Completed Month: {completedMonth.month}</h3>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 sm:gap-6">
                        <div className="bg-slate-50 p-3.5 sm:p-6 rounded-3xl border border-slate-100">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Month Start</p>
                          <p className="text-lg sm:text-2xl font-black text-slate-900">{completedMonth.start_pct?.toFixed(2)}%</p>
                        </div>
                        <div className="bg-slate-50 p-3.5 sm:p-6 rounded-3xl border border-slate-100">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Month End</p>
                          <p className="text-lg sm:text-2xl font-black text-slate-900">{completedMonth.end_pct?.toFixed(2)}%</p>
                        </div>
                        <div className="bg-emerald-50 p-3.5 sm:p-6 rounded-3xl border border-emerald-100">
                          <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest mb-2">Actual Production</p>
                          <p className="text-lg sm:text-2xl font-black text-emerald-600">+{completedMonth.actual_production?.toFixed(2)}%</p>
                        </div>
                        <div className="bg-indigo-50 p-3.5 sm:p-6 rounded-3xl border border-indigo-100">
                          <p className="text-[10px] font-black text-indigo-700 uppercase tracking-widest mb-2">Envisaged Production</p>
                          <p className="text-lg sm:text-2xl font-black text-indigo-600">{completedMonth.envisaged_production?.toFixed(2)}%</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Ongoing Month Recalibration */}
                  {ongoingMonth && (
                    <div>
                      <div className="flex items-center gap-2 mb-6">
                        <div className="w-2 h-2 bg-sunflower-gold-500 rounded-full animate-bounce" />
                        <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest">Ongoing Calibration: {ongoingMonth.month}</h3>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 sm:gap-6">
                        <div className="bg-slate-900 p-3.5 sm:p-6 rounded-3xl border border-slate-800 text-white shadow-2xl">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Current Total Progress</p>
                          <p className="text-xl sm:text-3xl font-black text-sunflower-gold-400 break-words">{ongoingMonth.end_pct?.toFixed(2)}%</p>
                          <p className="text-[10px] font-medium text-slate-500 mt-2">Status as of latest report</p>
                        </div>

                        <div className="bg-white p-3.5 sm:p-6 rounded-3xl border border-slate-100 shadow-xl group hover:border-vivid-tangerine-200 transition-all">
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Baseline Month Target</p>
                          <p className="text-xl sm:text-3xl font-black text-slate-900 break-words">{ongoingMonth.target_fixed_month_end?.toFixed(2)}%</p>
                          <p className="text-[10px] font-bold text-vivid-tangerine-50 mt-2">+{ongoingMonth.production_planned_fixed?.toFixed(2)}% Required</p>
                        </div>

                        <div className="bg-indigo-600 p-3.5 sm:p-6 rounded-3xl border border-indigo-500 text-white shadow-2xl group hover:scale-105 transition-all">
                          <p className="text-[10px] font-black text-indigo-200 uppercase tracking-widest mb-2">Recalibrated Target (Rolling)</p>
                          <p className="text-xl sm:text-3xl font-black text-white break-words">{ongoingMonth.target_rolling_month_end?.toFixed(2)}%</p>
                          <p className="text-[10px] font-bold text-indigo-200 mt-2">+{ongoingMonth.production_required_rolling?.toFixed(2)}% New Pace</p>
                        </div>

                        <div className="bg-sunflower-gold-500 p-3.5 sm:p-6 rounded-3xl border border-sunflower-gold-400 text-slate-900 shadow-2xl">
                          <p className="text-[10px] font-black text-slate-800 uppercase tracking-widest mb-2">Required Weekly Rate</p>
                          <p className="text-xl sm:text-3xl font-black text-white break-words">{ongoingMonth.required_weekly?.toFixed(2)}% <span className="text-xs sm:text-sm font-bold">/ week</span></p>
                          <p className="text-[10px] font-black text-slate-800 mt-2">RECALIBRATED VELOCITY</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="bg-slate-900 rounded-[2.5rem] p-4 sm:p-8 text-white relative overflow-hidden shadow-2xl border border-white/5">
                    <div className="absolute top-0 right-0 p-6 opacity-10">
                      <TrendingUp className="w-20 h-20 text-sunflower-gold-500" />
                    </div>
                    <div className="flex items-start gap-0 sm:gap-6 relative z-10">
                      <div className="p-3 bg-sunflower-gold-500/20 rounded-2xl hidden sm:block">
                        <AlertTriangle className="w-6 h-6 text-sunflower-gold-400" />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-2">Recalibration Executive Summary</p>
                        <p className="text-base leading-relaxed text-white/90 font-medium max-w-4xl">
                          Analysis of the last completed month (<strong>{completedMonth?.month}</strong>) shows the project achieved <strong>{completedMonth?.actual_production}%</strong> production against an envisaged S-curve target of <strong>{completedMonth?.envisaged_production}%</strong>.
                          <br /><br />
                          As of the latest live report in mid-{ongoingMonth?.month.split(' ')[0]}, the cumulative variance has widened to <span className="text-sunflower-gold-400 font-black">{Math.abs(variance).toFixed(2)}%</span> behind the project baseline S-curve.
                          To hit the newly recalibrated milestone of <strong>{ongoingMonth?.target_rolling_month_end}%</strong> by {ongoingMonth?.month} {ongoingMonth?.month ? getMonthLastDay(ongoingMonth.month) : '31st'}, the contractor must maintain a strict velocity of
                          <span className="text-sunflower-gold-400 font-black"> {ongoingMonth?.required_weekly}% per week</span> for the remainder of {ongoingMonth?.month}.
                        </p>

                        <div className="mt-6 pt-6 border-t border-white/10">
                          <p className="text-[10px] font-black text-sunflower-gold-400 uppercase tracking-widest mb-2">P.S. Mathematical Logic & S-Curve Forgiveness</p>
                          <p className="text-[11px] text-white/60 leading-relaxed italic">
                            The <span className="text-white font-bold">{Math.abs(variance).toFixed(2)}% variance</span> represents the true cumulative S-curve progress deficit. The S-curve expected progress to be at <strong>{latestWeek?.envisaged_pct_work?.toFixed(2)}%</strong>, but actual progress is <strong>{latestWeek?.pct_work?.toFixed(2)}%</strong>.
                            <br /><br />
                            This is fundamentally distinct from the pure calendar <span className="text-white font-bold">Slippage Gap of {latestWeek?.slippage_gap?.toFixed(2)}%</span> (which is the elapsed project time of <strong>{latestWeek?.pct_time?.toFixed(2)}%</strong> minus work completed). If the system used a straight linear mathematical baseline, the contractor would be heavily penalized for the naturally slow site mobilization phase, and the deficit would incorrectly match the massive {latestWeek?.slippage_gap?.toFixed(2)}% slippage gap.
                            <br /><br />
                            Instead, the mathematical S-Curve mathematically forgives the slow start. It calculates that the project was only ever expected to be at {latestWeek?.envisaged_pct_work?.toFixed(2)}% by this date. This true, realistic {Math.abs(variance).toFixed(2)}% backlog is the exact mathematical deficit that forced the required weekly velocity to shift from the original baseline up to the current <strong>{ongoingMonth?.required_weekly}%</strong> in order to recover the timeline.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </section>

          {/* Production Recalibration Chain Table */}
          <section className="bg-white rounded-[2rem] p-4 sm:p-10 border border-slate-100 shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
            <div className="flex items-center gap-3 mb-8">
              <Layers className="text-vivid-tangerine-600 w-6 h-6" />
              <h2 className="text-2xl font-bold">Production Recalibration Chain</h2>
            </div>

            <div className="overflow-x-auto rounded-[2rem] border border-slate-100">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="p-2 sm:p-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Reporting Week</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Start %</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">End %</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-emerald-600 uppercase tracking-widest text-right">Actual (x)</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-indigo-600 uppercase tracking-widest text-right">Envisaged (y)</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-slate-900 uppercase tracking-widest text-right">Variance (k)</th>
                    <th className="p-2 sm:p-4 text-[10px] font-black text-sunflower-gold-600 uppercase tracking-widest text-right">Recalibrated (New y)</th>
                  </tr>
                </thead>
                <tbody>
                  {(financials?.weekly_financials || []).map((w: any, i: number) => (
                    <tr key={i} className="border-t border-slate-50 hover:bg-slate-50/50 transition-colors group">
                      <td className="p-2 sm:p-4">
                        <p className="text-xs font-bold text-slate-700">{w.label}</p>
                      </td>
                      <td className="p-2 sm:p-4 text-right">
                        <p className="text-xs font-medium text-slate-400">{w.start_pct?.toFixed(2)}%</p>
                      </td>
                      <td className="p-2 sm:p-4 text-right">
                        <p className="text-xs font-black text-slate-900">{w.end_pct?.toFixed(2)}%</p>
                      </td>
                      <td className="p-2 sm:p-4 text-right bg-emerald-50/20">
                        <p className="text-xs font-black text-emerald-600">{w.weekly_actual?.toFixed(2)}%</p>
                      </td>
                      <td className="p-2 sm:p-4 text-right bg-indigo-50/20">
                        <p className="text-xs font-black text-indigo-600">{w.weekly_envisaged?.toFixed(2)}%</p>
                      </td>
                      <td className="p-2 sm:p-4 text-right">
                        <span className={`text-[10px] font-black px-2 py-1 rounded-md ${w.weekly_variance >= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                          {w.weekly_variance >= 0 ? '+' : ''}{w.weekly_variance?.toFixed(2)}%
                        </span>
                      </td>
                      <td className="p-2 sm:p-4 text-right bg-sunflower-gold-50/30">
                        <p className="text-xs font-black text-sunflower-gold-600">{w.required_future_rate?.toFixed(2)}%</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 p-4 bg-slate-900 rounded-2xl text-[10px] text-white/60 font-medium">
              <span className="text-sunflower-gold-400 font-black">LOGIC:</span> Actual (x) is current production. Envisaged (y) is the required rate for that week based on remaining balance. Variance (k) = x - y. Recalibrated is the new target rate for the following week.
            </div>
          </section>

        </div>

        {/* Stakeholder Recommendations */}
        <section className="bg-white rounded-[2rem] p-5 sm:p-12 border border-slate-100 shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
          <div className="flex items-center gap-3 mb-10">
            <Users className="text-vivid-tangerine-600 w-7 h-7" />
            <h2 className="text-2xl font-extrabold">Strategic Recommendations</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-lg">PM</div>
                <h3 className="font-bold text-slate-900">Advice to Project Manager</h3>
              </div>
              <div className="space-y-4">
                {insights?.recommendations?.to_client?.map((r: string, i: number) => (
                  <div key={i} className="flex gap-2.5 sm:gap-4 p-3.5 sm:p-5 bg-slate-50 rounded-2xl border border-slate-100 items-start group hover:border-vivid-tangerine-200 transition-colors">
                    <span className="text-vivid-tangerine-500 font-black text-lg">0{i + 1}</span>
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
                  <div key={i} className="flex gap-2.5 sm:gap-4 p-3.5 sm:p-5 bg-vivid-tangerine-50/30 rounded-2xl border border-vivid-tangerine-100/50 items-start group hover:border-vivid-tangerine-300 transition-colors">
                    <span className="text-vivid-tangerine-600 font-black text-lg">0{i + 1}</span>
                    <p className="text-sm text-slate-600 font-medium leading-relaxed">{r}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Global Verdict Card */}
        <section className="mt-12">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[3rem] p-5 sm:p-12 text-white flex flex-col md:flex-row justify-between items-center gap-4 sm:gap-8 relative overflow-hidden">
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
              <button
                onClick={handleGenerateProgress}
                disabled={generatingProgress || !isAdmin}
                className={`px-8 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${!isAdmin
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                  : 'bg-white text-slate-900 hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed'
                  }`}
              >
                {!isAdmin ? (
                  <>
                    <span>🔒</span>
                    <span>Progress Report Generator Locked</span>
                  </>
                ) : generatingProgress ? (
                  <>
                    <div className="w-3 h-3 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <span>Generate Full Progress Report</span>
                )}
              </button>
            </div>
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-48 h-48 rounded-full border-8 border-white/5 flex items-center justify-center relative">
                <div className="absolute inset-4 rounded-full border-8 border-vivid-tangerine-500/20"></div>
                <div className="text-center">
                  <p className="text-5xl font-black mb-1">{Math.max(0, Math.round(globalProgress.time - globalProgress.work))}%</p>
                  <p className="text-[8px] font-bold uppercase tracking-widest text-slate-400">Risk Variance</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Progress Intelligence Modal */}
      {showProgressModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-[3rem] w-full max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-300 flex flex-col">
            <div className="bg-slate-900 p-8 text-white relative shrink-0">
              <div className="absolute top-0 right-0 w-64 h-64 bg-vivid-tangerine-500/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
              <div className="relative z-10 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="text-emerald-400 w-5 h-5" />
                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-400">Intelligence Ready</span>
                  </div>
                  <h2 className="text-3xl font-black tracking-tight">Progress Workspace</h2>
                </div>
                <button
                  onClick={() => setShowProgressModal(false)}
                  className="p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                  <ArrowRight className="w-6 h-6 rotate-45" />
                </button>
              </div>
            </div>

            <div className="p-10 overflow-y-auto custom-scrollbar flex-1">
              <div className="grid grid-cols-2 gap-6 mb-10">
                <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Risk Verdict</p>
                  <p className={`text-2xl font-black ${insights?.claim_verdict === 'High' ? 'text-rose-500' : 'text-sunflower-gold-500'}`}>
                    {insights?.claim_verdict}
                  </p>
                </div>
                <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Slippage Progress Analysis</p>
                  <p className="text-2xl font-black text-slate-900">
                    {(globalProgress.time - globalProgress.work).toFixed(2)}%
                  </p>
                </div>
              </div>

              <div className="space-y-8 mb-10">
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Executive Summary</p>
                  <p className="text-sm text-slate-600 leading-relaxed italic border-l-4 border-vivid-tangerine-500 pl-6 py-1">
                    {insights?.executive_summary}
                  </p>
                </div>

                {/* Detailed SWOT Grid */}
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Detailed Intelligence Scan</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-50/50 p-6 rounded-2xl border border-emerald-100">
                      <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-3">Strengths</p>
                      <ul className="space-y-2">
                        {insights?.swot?.strengths?.map((s: string, i: number) => (
                          <li key={i} className="text-[11px] text-emerald-800 flex gap-2 font-medium"><span>•</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-rose-50/50 p-6 rounded-2xl border border-rose-100">
                      <p className="text-[9px] font-black text-rose-600 uppercase tracking-widest mb-3">Threats</p>
                      <ul className="space-y-2">
                        {insights?.swot?.threats?.map((s: string, i: number) => (
                          <li key={i} className="text-[11px] text-rose-800 flex gap-2 font-medium"><span>•</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-amber-50/50 p-6 rounded-2xl border border-amber-100">
                      <p className="text-[9px] font-black text-amber-600 uppercase tracking-widest mb-3">Weaknesses</p>
                      <ul className="space-y-2">
                        {insights?.swot?.weaknesses?.map((s: string, i: number) => (
                          <li key={i} className="text-[11px] text-amber-800 flex gap-2 font-medium"><span>•</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-blue-50/50 p-6 rounded-2xl border border-blue-100">
                      <p className="text-[9px] font-black text-blue-600 uppercase tracking-widest mb-3">Opportunities</p>
                      <ul className="space-y-2">
                        {insights?.swot?.opportunities?.map((s: string, i: number) => (
                          <li key={i} className="text-[11px] text-blue-800 flex gap-2 font-medium"><span>•</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Recommendations Preview */}
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Strategic Recommendations</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-6 bg-slate-900 rounded-[2rem] text-white">
                      <p className="text-[8px] font-black text-vivid-tangerine-400 uppercase tracking-widest mb-3">Advice to Client (PM)</p>
                      <ul className="space-y-2">
                        {insights?.recommendations?.to_client?.map((r: string, i: number) => (
                          <li key={i} className="text-[10px] text-slate-300 flex gap-2"><span>→</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-6 bg-vivid-tangerine-50 rounded-[2rem] border border-vivid-tangerine-100">
                      <p className="text-[8px] font-black text-vivid-tangerine-600 uppercase tracking-widest mb-3">Directives to Contractor</p>
                      <ul className="space-y-2">
                        {insights?.recommendations?.to_contractor?.map((r: string, i: number) => (
                          <li key={i} className="text-[10px] text-slate-600 flex gap-2 font-medium"><span>•</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Professional Financial Exposure (Calculated) */}
                <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full -mr-16 -mt-16"></div>
                  <div className="relative z-10">
                    <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest mb-4">Financial Exposure Analysis</p>
                    <div className="flex justify-between items-end">
                      <div>
                        <p className="text-[9px] text-slate-400 uppercase mb-1">Estimated Revenue Earned</p>
                        <p className="text-2xl font-black text-white">
                          KES {(2127050827.72 * (globalProgress.work / 100) || 0).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[9px] text-slate-400 uppercase mb-1">Contract Valuation</p>
                        <p className="text-sm font-bold text-slate-300">KES 2.127B</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-8 bg-slate-50 border-t border-slate-100 shrink-0">
              <button
                onClick={downloadProgressReport}
                disabled={downloadingDoc}
                className={`w-full py-5 rounded-[2rem] font-black text-sm uppercase tracking-[0.2em] transition-all shadow-xl ${downloadingDoc
                  ? 'bg-slate-400 cursor-not-allowed shadow-none text-white'
                  : 'bg-vivid-tangerine-500 hover:bg-vivid-tangerine-600 shadow-vivid-tangerine-500/20 text-white hover:scale-[1.02] active:scale-95'
                  }`}
              >
                {downloadingDoc ? (
                  'Generating DOCX... Please Wait'
                ) : (
                  'Download Full .DOCX Report'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          height: 4px;
          width: 4px;
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

      {/* Footer Panel */}
      <footer className="mt-20 border-t border-slate-100 pt-12 pb-8 max-w-7xl mx-auto px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-left">
            <p className="text-xs font-black text-slate-900 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter mb-4 md:mb-0">Field Intelligence & Reporting</p>

            {/* NeuralAxis Labs Branding Logo */}
            <div className="flex items-center gap-2.5 mt-4">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
              <span className="text-xs font-black text-slate-950 tracking-tight">NeuralAxis Labs</span>
            </div>
          </div>
          <div className="flex flex-col items-stretch md:items-end gap-3">
            <div className="flex justify-center md:justify-end gap-4">
              <Link href="/" className="text-xs font-bold text-slate-600 hover:text-vivid-tangerine-600 transition-colors">Home</Link>
              <Link href="/dashboard" className="text-xs font-bold text-slate-600 hover:text-vivid-tangerine-600 transition-colors">Dashboard</Link>
              <Link href="/contract" className="text-xs font-bold text-slate-600 hover:text-vivid-tangerine-600 transition-colors">Contract</Link>
            </div>
            <div className="flex justify-center md:justify-end gap-3">
              <Link href="/terms" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-slate-50 border border-slate-100 px-3 py-1 rounded-full">Terms</Link>
              <Link href="/privacy" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-slate-50 border border-slate-100 px-3 py-1 rounded-full">Privacy</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 text-center border-t border-slate-50 pt-6">
          <p className="text-[10px] text-slate-300 font-bold uppercase tracking-widest">&copy; 2026 Makindu Affordable Housing Project. All Rights Reserved.</p>
        </div>
      </footer>

      {isRegenerating && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-[9999] flex flex-col items-center justify-center p-6 transition-all duration-300">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 max-w-md w-full text-center relative overflow-hidden shadow-2xl">
            <div className="absolute -right-20 -top-20 w-60 h-60 bg-sunflower-gold-500/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute -left-20 -bottom-20 w-60 h-60 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="relative z-10">
              <div className="w-20 h-20 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-8 shadow-2xl relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-tr from-sunflower-gold-500/20 to-vivid-tangerine-500/20 animate-pulse" />
                <Loader2 className="w-10 h-10 text-sunflower-gold-400 animate-spin relative z-10" />
              </div>

              <h3 className="text-2xl font-black text-white mb-3">AI Engine Processing</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-8">
                AI Engine is analyzing the full trend history, project correspondence, and financial calibration data to generate strategic insights...
              </p>

              <div className="flex flex-col gap-2">
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-500 rounded-full w-4/5 animate-pulse" />
                </div>
                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                  Synthesizing SWOT & Recommendations
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}