"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth, useUser, UserButton } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function ContractSummary() {
  const router = useRouter();
  const { isLoaded, userId, getToken, signOut } = useAuth();
  const { user } = useUser();

  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);
  const [isVerifyingAccess, setIsVerifyingAccess] = useState(() => {
    if (typeof window !== 'undefined') {
      return !sessionStorage.getItem('allowed_user');
    }
    return true;
  });

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
  }, []);

  // Authentication Guard Redirect
  useEffect(() => {
    if (mounted && isLoaded && !userId) {
      router.replace('/login?redirect=/contract');
    }
  }, [mounted, isLoaded, userId, router]);

  useEffect(() => {
    if (isLoaded && userId) {
      fetchSummary();
    }
  }, [isLoaded, userId]);

  const fetchSummary = async () => {
    try {
      const token = await getToken();
      const resp = await fetch(`${BACKEND_URL}/api/contract-summary`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (resp.status === 403) {
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('allowed_user');
        }
        await signOut({ redirectUrl: '/?error=not-allowed' });
        return;
      }
      if (resp.ok) {
        const data = await resp.json();
        if (data.msg && !data.project_title) {
          setSummary(null);
        } else {
          setSummary(data);
        }
        if (typeof window !== 'undefined' && userId) {
          sessionStorage.setItem('allowed_user', userId);
        }
        setIsVerifyingAccess(false);
      } else {
        setIsVerifyingAccess(false);
      }
    } catch (e) {
      setError('Failed to fetch contract summary.');
      setIsVerifyingAccess(false);
    } finally {
      setLoading(false);
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
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-900 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-750 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-2.5 sm:px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center gap-1.5 self-start">
            <svg className="w-4 h-4 text-vivid-tangerine-500" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </Link>
          <div className="flex items-center gap-2 self-stretch sm:self-auto justify-between sm:justify-start">
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
            <Link href="/" className="text-xs font-bold text-vivid-tangerine-700 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-2.5 sm:px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center justify-center">
              Home
            </Link>
          </div>
        </div>

        <h1 className="text-2xl sm:text-4xl font-bold mb-6 sm:mb-8 font-serif bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent break-words">
          Project Contract Details
        </h1>



        {error && (
          <div className="bg-vivid-tangerine-50 p-6 rounded-2xl border border-vivid-tangerine-200 text-vivid-tangerine-900 mb-8">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl shadow-lg border border-vanilla-custard-100">
            <div className="w-12 h-12 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-sm font-bold text-vivid-tangerine-800 uppercase tracking-wider animate-pulse">Fetching contract details...</p>
          </div>
        ) : summary ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1 sm:gap-6">
            <div className="md:col-span-2 bg-white p-4 sm:p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-2">Project Title</h2>
              <p className="text-lg sm:text-2xl font-bold text-vivid-tangerine-950 break-words">{summary.project_title}</p>
            </div>

            {([
              { label: 'Contract No', value: summary.contract_no },
              { label: 'Employer', value: summary.employer },
              { label: 'Contractor', value: summary.contractor },
              { label: 'Consultant', value: summary.consultant },
              { label: 'Contract Sum', value: summary.contract_sum },
              { label: 'Contract Period', value: summary.contract_period },
              { label: 'Possession Date', value: summary.possession_date },
              { label: 'Commencement Date', value: summary.commencement_date },
              { label: 'Completion Date', value: summary.completion_date },
              { label: 'Location', value: summary.location },
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-4 sm:p-6 rounded-2xl shadow-md border border-vanilla-custard-50">
                <h3 className="text-[10px] font-bold text-vivid-tangerine-400 uppercase tracking-tighter mb-1">{item.label}</h3>
                <p className="text-sm sm:text-base font-semibold text-vivid-tangerine-900 break-words">{item.value || 'N/A'}</p>
              </div>
            )))}

            <div className="md:col-span-2 bg-white p-4 sm:p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Scope of Works</h2>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {summary.scope_of_works?.map((work: string, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-sm font-medium text-vivid-tangerine-800">
                    <span className="text-sunflower-gold-500">✔</span> {work}
                  </li>
                ))}
              </ul>
            </div>

            <div className="md:col-span-2 bg-white p-4 sm:p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Socio-Economic Impact</h2>
              <p className="text-xs sm:text-sm text-vivid-tangerine-800 leading-relaxed italic break-words">
                "{summary.socio_economic_impact}"
              </p>
            </div>

            <div className="md:col-span-2 bg-white p-4 sm:p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Insurance Policies</h2>
              <div className="overflow-hidden rounded-2xl border border-vanilla-custard-100">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-vanilla-custard-50">
                      <th className="p-2 sm:p-4 text-[10px] sm:text-xs font-bold text-vivid-tangerine-800 uppercase">Policy Description</th>
                      <th className="p-2 sm:p-4 text-[10px] sm:text-xs font-bold text-vivid-tangerine-800 uppercase">Expiry Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.insurances?.map((ins: any, i: number) => (
                      <tr key={i} className="border-t border-vanilla-custard-100 hover:bg-vanilla-custard-50/50 transition-colors">
                        <td className="p-2 sm:p-4 text-xs sm:text-sm font-medium text-vivid-tangerine-900 break-words">{ins.policy}</td>
                        <td className="p-2 sm:p-4 text-xs sm:text-sm font-bold text-vivid-tangerine-700 break-words">{ins.expiry}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Footer Panel */}
      <footer className="mt-20 border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-left">
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
            <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4 md:mb-0">Field Reporting &amp; Analytics</p>

            {/* NeuralAxis Labs Branding Logo */}
            <div className="flex items-center gap-2.5 mt-4">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <a href="https://neuralaxislabs.online" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
                <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
              </a>
            </div>
          </div>
          <div className="flex flex-col items-stretch md:items-end gap-3">
            <div className="flex justify-center md:justify-end gap-4">
              <Link href="/" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Home</Link>
              <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Dashboard</Link>
              <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Trends</Link>
            </div>
            <div className="flex justify-center md:justify-end gap-3">
              <Link href="/terms" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-vanilla-custard-100/30 border border-vanilla-custard-200 px-3 py-1 rounded-full">Terms</Link>
              <Link href="/privacy" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-vanilla-custard-100/30 border border-vanilla-custard-200 px-3 py-1 rounded-full">Privacy</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 text-center border-t border-vanilla-custard-100 pt-6">
          <p className="text-[10px] text-vanilla-custard-400 font-bold uppercase tracking-widest">&copy; 2026 Makindu Affordable Housing Project. All Rights Reserved.</p>
        </div>
      </footer>
    </main>
  );
}
