"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth, useUser, UserButton } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';

export default function ContractSummary() {
  const router = useRouter();
  const { isLoaded, userId, getToken } = useAuth();
  const { user } = useUser();

  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  // Client-side Role Checking
  const userEmail = user?.primaryEmailAddress?.emailAddress;
  const adminEmail = process.env.NEXT_PUBLIC_ADMIN_EMAIL || '';
  const isAdmin = userEmail && adminEmail && userEmail.toLowerCase() === adminEmail.toLowerCase();

  // Handle client-side mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // Authentication Guard Redirect
  useEffect(() => {
    if (mounted && isLoaded && !userId) {
      router.replace('/login');
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
      const resp = await fetch('http://localhost:8000/api/contract-summary', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (data.msg && !data.project_title) {
        setSummary(null);
      } else {
        setSummary(data);
      }
    } catch (e) {
      setError('Failed to fetch contract summary.');
    } finally {
      setLoading(false);
    }
  };

  if (!isLoaded || !userId) {
    return (
      <div className="min-h-screen bg-vanilla-custard-50 flex flex-col items-center justify-center text-vivid-tangerine-950">
        <div className="w-16 h-16 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold text-vivid-tangerine-800 uppercase tracking-widest animate-pulse">Loading Security Context...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-900 p-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-750 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center gap-1.5">
            <svg className="w-4 h-4 text-vivid-tangerine-500" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </Link>
          <div className="flex items-center gap-3 self-stretch sm:self-auto justify-between sm:justify-start">
            {!isAdmin ? (
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50/80 border border-amber-200 px-3.5 py-2 rounded-xl shadow-sm">
                Viewer Access
              </span>
            ) : (
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50/80 border border-emerald-200 px-3.5 py-2 rounded-xl shadow-sm">
                Admin Access
              </span>
            )}
            <UserButton 
              afterSignOutUrl="/login" 
              appearance={{
                elements: {
                  avatarBox: "w-9 h-9 border border-vivid-tangerine-200/80 shadow-md hover:scale-105 transition-transform duration-200",
                }
              }}
            />
            <Link href="/" className="text-xs font-bold text-vivid-tangerine-700 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center justify-center">
              Home
            </Link>
          </div>
        </div>
        
        <h1 className="text-4xl font-bold mb-8 font-serif bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent">
          Project Contract Details
        </h1>

        {loading && (
          <div className="text-center p-12">
            <p className="text-vivid-tangerine-600 animate-pulse font-bold">Loading project data...</p>
          </div>
        )}

        {error && (
          <div className="bg-vivid-tangerine-50 p-6 rounded-2xl border border-vivid-tangerine-200 text-vivid-tangerine-900 mb-8">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2 bg-white p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-2">Project Title</h2>
              <p className="text-2xl font-bold text-vivid-tangerine-950">{summary.project_title}</p>
            </div>

            {[
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
              <div key={idx} className="bg-white p-6 rounded-2xl shadow-md border border-vanilla-custard-50">
                <h3 className="text-[10px] font-bold text-vivid-tangerine-400 uppercase tracking-tighter mb-1">{item.label}</h3>
                <p className="font-semibold text-vivid-tangerine-900">{item.value || 'N/A'}</p>
              </div>
            ))}

            <div className="md:col-span-2 bg-white p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Scope of Works</h2>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {summary.scope_of_works?.map((work: string, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-sm font-medium text-vivid-tangerine-800">
                    <span className="text-sunflower-gold-500">✔</span> {work}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="md:col-span-2 bg-white p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Socio-Economic Impact</h2>
              <p className="text-sm text-vivid-tangerine-800 leading-relaxed italic">
                "{summary.socio_economic_impact}"
              </p>
            </div>

            <div className="md:col-span-2 bg-white p-8 rounded-3xl shadow-lg border border-vanilla-custard-100">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4">Insurance Policies</h2>
              <div className="overflow-hidden rounded-2xl border border-vanilla-custard-100">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-vanilla-custard-50">
                      <th className="p-4 text-xs font-bold text-vivid-tangerine-800 uppercase">Policy Description</th>
                      <th className="p-4 text-xs font-bold text-vivid-tangerine-800 uppercase">Expiry Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.insurances?.map((ins: any, i: number) => (
                      <tr key={i} className="border-t border-vanilla-custard-100 hover:bg-vanilla-custard-50/50 transition-colors">
                        <td className="p-4 text-sm font-medium text-vivid-tangerine-900">{ins.policy}</td>
                        <td className="p-4 text-sm font-bold text-vivid-tangerine-700">{ins.expiry}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Panel */}
      <footer className="mt-20 border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-left">
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
            <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4 md:mb-0">Field Intelligence & Reporting</p>
            
            {/* NeuralAxis Labs Branding Logo */}
            <div className="flex items-center gap-2.5 mt-4">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
              <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
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
