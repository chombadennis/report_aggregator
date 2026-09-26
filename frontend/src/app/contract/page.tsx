"use client";
import React, { useState, useEffect } from 'react';
import { Search, Loader2, PlayCircle, Save } from 'lucide-react';
import NavigationPanel from '@/components/NavigationPanel';
import RevealWrapper from '@/components/animations/RevealWrapper';
import Link from 'next/link';
import { useAuth, useUser, UserButton } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function ContractSummary() {
  const router = useRouter();
  const { isLoaded, userId, getToken, signOut } = useAuth();
  const { user } = useUser();

  const [summary, setSummary] = useState<any>(null);
  const [evmData, setEvmData] = useState<any>({});
  const [selectedWeek, setSelectedWeek] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateStatus, setUpdateStatus] = useState('');
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [originalEvmData, setOriginalEvmData] = useState<any>(null);
  const [financials, setFinancials] = useState<any>(null);
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
        
        // Fetch EVM Data
        try {
          const evmResp = await fetch(`${BACKEND_URL}/api/contracts-evm`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (evmResp.ok) {
            const evmJson = await evmResp.json();
            setEvmData(evmJson);
            setOriginalEvmData(JSON.parse(JSON.stringify(evmJson)));
            const weeks = Object.keys(evmJson);
            if (weeks.length > 0) {
              setSelectedWeek(weeks.sort((a, b) => b.localeCompare(a))[0]); // roughly latest
            }
          }
        } catch (evmErr) {
          console.error("Failed to fetch EVM data", evmErr);
        }

        // Fetch Financials Analytics for Progress %
        try {
          const finResp = await fetch(`${BACKEND_URL}/api/analytics/financials`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (finResp.ok) {
            const finJson = await finResp.json();
            setFinancials(finJson);
          }
        } catch (finErr) {
          console.error("Failed to fetch financials data", finErr);
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

  const handleUpdateEVM = async () => {
    if (!selectedWeek || !evmData[selectedWeek]) return;
    setIsUpdating(true);
    setUpdateStatus('Updating EVM Data...');
    try {
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/contracts-evm`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          week_name: selectedWeek,
          data: evmData[selectedWeek]
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update EVM data');
      }

      setUpdateStatus('✅ EVM Data Updated successfully!');
      setOriginalEvmData(JSON.parse(JSON.stringify(evmData)));
      setIsEditing(false);
      setShowUpdateModal(true);
    } catch (err: any) {
      setUpdateStatus('❌ Error updating EVM Data');
      setShowUpdateModal(true);
    } finally {
      setIsUpdating(false);
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
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-900">
      <NavigationPanel />
      <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8 pt-4 sm:pt-8">

        <h1 className="text-2xl sm:text-3xl font-bold mb-6 font-serif bg-gradient-to-r from-deep-space-blue-600 via-vivid-tangerine-500 to-sunflower-gold-500 bg-clip-text text-transparent break-words">
          Contracts & EVM
        </h1>



        {error && (
          <div className="bg-vivid-tangerine-50 p-6 rounded-none border border-vivid-tangerine-200 text-vivid-tangerine-900 mb-8">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <RevealWrapper>
            <div className="flex flex-col items-center justify-center py-20 bg-white rounded-none shadow-lg border border-vanilla-custard-100">
              <div className="w-12 h-12 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm font-bold text-vivid-tangerine-800 uppercase tracking-wider animate-pulse">Fetching contract details...</p>
            </div>
          </RevealWrapper>
        ) : summary ? (
          <RevealWrapper direction="up" delay={0.1}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
            <div className="md:col-span-2 bg-white/80 backdrop-blur-sm p-4 sm:p-8 rounded-none shadow-lg hover:shadow-xl border border-vanilla-custard-100 hover:border-vivid-tangerine-200 transition-all duration-300 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                <span className="text-lg">🏗️</span> Project Title
              </h2>
              <p className="text-lg sm:text-2xl font-bold text-vivid-tangerine-950 break-words group-hover:text-vivid-tangerine-600 transition-colors relative z-10">{summary.project_title}</p>
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
              <div key={idx} className="bg-white/90 hover:bg-gradient-to-br hover:from-white hover:to-vanilla-custard-50 p-4 sm:p-5 rounded-none shadow-sm hover:shadow-md hover:-translate-y-1 border border-vanilla-custard-100 transition-all duration-300 group cursor-default relative overflow-hidden">
                <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-vanilla-custard-200/20 to-transparent rounded-bl-full transform translate-x-1/2 -translate-y-1/2 group-hover:scale-150 transition-transform duration-500" />
                <h3 className="text-[10px] font-bold text-vivid-tangerine-400 uppercase tracking-tighter mb-1 group-hover:text-vivid-tangerine-500 transition-colors relative z-10">{item.label}</h3>
                <p className="text-sm sm:text-base font-semibold text-vivid-tangerine-900 break-words group-hover:text-deep-space-blue-900 transition-colors relative z-10">{item.value || 'N/A'}</p>
              </div>
            )))}

            <RevealWrapper>
            <div className="md:col-span-2 bg-white/80 backdrop-blur-sm p-4 sm:p-8 rounded-none shadow-lg hover:shadow-xl border border-vanilla-custard-100 hover:border-sunflower-gold-200 transition-all duration-300 group">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-lg">📋</span> Scope of Works
              </h2>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {summary.scope_of_works?.map((work: string, i: number) => (
                  <li key={i} className="flex items-center gap-3 text-sm font-medium text-vivid-tangerine-800 bg-vanilla-custard-50/50 p-2.5 rounded-none border border-vanilla-custard-100/50 hover:bg-white transition-colors">
                    <span className="text-sunflower-gold-500 bg-sunflower-gold-50 rounded-full p-1 shadow-sm">✔</span> {work}
                  </li>
                ))}
              </ul>
            </div>
            </RevealWrapper>

            <div className="md:col-span-2 bg-gradient-to-br from-vivid-tangerine-600 to-vivid-tangerine-800 p-4 sm:p-8 rounded-none shadow-lg hover:shadow-2xl hover:scale-[1.01] transition-all duration-300 text-white overflow-hidden relative group">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2 group-hover:scale-150 transition-transform duration-700" />
              <h2 className="text-xs font-bold text-vivid-tangerine-200 uppercase tracking-widest mb-4 flex items-center gap-2 relative z-10">
                <span className="text-lg">🌍</span> Socio-Economic Impact
              </h2>
              <p className="text-sm sm:text-base text-white/95 leading-relaxed italic break-words relative z-10 font-medium">
                "{summary.socio_economic_impact}"
              </p>
            </div>

            <RevealWrapper>
            <div className="md:col-span-2 bg-white/80 backdrop-blur-sm p-4 sm:p-8 rounded-none shadow-lg hover:shadow-xl border border-vanilla-custard-100 transition-all duration-300">
              <h2 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                <span className="text-lg">🛡️</span> Insurance Policies
              </h2>
              <div className="overflow-hidden rounded-none border border-vanilla-custard-100 shadow-inner">
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
            </RevealWrapper>

            <div className="md:col-span-2 bg-white/80 backdrop-blur-sm p-4 sm:p-8 rounded-none shadow-xl hover:shadow-2xl border border-vanilla-custard-100 hover:border-vivid-tangerine-300 transition-all duration-300 relative overflow-hidden mt-8 group">
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-sunflower-gold-200/30 to-vivid-tangerine-300/20 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2 group-hover:scale-125 transition-transform duration-700 pointer-events-none" />
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4 relative z-10">
                <h2 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-deep-space-blue-700 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif flex items-center gap-3">
                  <span className="text-2xl">📈</span> Earned Value Management
                </h2>
                {Object.keys(evmData).length > 0 && (
                  <select
                    value={selectedWeek}
                    onChange={(e) => {
                      setSelectedWeek(e.target.value);
                      if (isEditing) {
                        setEvmData(JSON.parse(JSON.stringify(originalEvmData)));
                        setIsEditing(false);
                      }
                    }}
                    className="bg-vanilla-custard-50 border border-vanilla-custard-200 text-vivid-tangerine-900 text-sm font-bold rounded-none px-4 py-2 outline-none focus:border-vivid-tangerine-500 shadow-sm"
                  >
                    {Object.keys(evmData).sort((a, b) => b.localeCompare(a)).map(w => (
                      <option key={w} value={w}>{w}</option>
                    ))}
                  </select>
                )}
              </div>

              {selectedWeek && evmData[selectedWeek] && evmData[selectedWeek].start_date && (
                <div className="mb-6 flex flex-wrap gap-4">
                  <div className="bg-vanilla-custard-50/50 p-3 rounded-none border border-vanilla-custard-100 inline-block">
                    <span className="text-[10px] font-bold text-vivid-tangerine-500 uppercase tracking-widest block mb-1">Reporting Period</span>
                    <p className="text-sm font-semibold text-vivid-tangerine-900">
                      {evmData[selectedWeek].start_date} <span className="text-vivid-tangerine-400 mx-2">➔</span> {evmData[selectedWeek].end_date}
                    </p>
                  </div>
                  
                  {/* Overall Progress Indicator */}
                  {(() => {
                    let matchedWeek = null;
                    if (financials?.weekly_financials && evmData[selectedWeek]?.start_date) {
                      const startDateStr = evmData[selectedWeek].start_date;
                      const dayMatch = startDateStr.match(/(\d+)/);
                      const monthMatch = startDateStr.match(/[a-zA-Z]+/);
                      
                      if (dayMatch && monthMatch) {
                        const day = dayMatch[0];
                        const month = monthMatch[0].toLowerCase().substring(0, 3);
                        
                        matchedWeek = financials.weekly_financials.find((w: any) => {
                          if (!w.label) return false;
                          const lbl = w.label.toLowerCase();
                          const hasMonth = lbl.includes(month);
                          const dayRegex = new RegExp(`(^|\\D)${day}(st|nd|rd|th)?(\\D|$)`, 'i');
                          return hasMonth && dayRegex.test(lbl);
                        });
                      }
                    }
                    
                    return (
                      <div className="bg-white/80 p-3 rounded-none border border-vanilla-custard-100 inline-block shadow-sm">
                        <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest block mb-1">Overall Progress</span>
                        <p className="text-sm font-black text-emerald-700">
                          {matchedWeek?.end_pct != null ? `${matchedWeek.end_pct.toFixed(2)}%` : 'Pending'}
                        </p>
                      </div>
                    );
                  })()}
                </div>
              )}

              {Object.keys(evmData).length === 0 ? (
                <div className="text-center py-10 bg-vanilla-custard-50 rounded-none border border-dashed border-vanilla-custard-200 text-vivid-tangerine-600 font-medium">
                  No EVM data recorded yet. Go to the Dashboard to input data.
                </div>
              ) : selectedWeek && evmData[selectedWeek] ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10">
                  <div className="overflow-x-auto bg-white/90 rounded-none border border-vanilla-custard-100 shadow-md hover:shadow-lg transition-all duration-300">
                    <h3 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest bg-gradient-to-r from-vanilla-custard-50 to-white p-4 border-b border-vanilla-custard-100">Component Progress</h3>
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-vanilla-custard-200 text-[10px] text-vivid-tangerine-800 uppercase tracking-wider bg-vanilla-custard-50/50">
                          <th className="p-3">Component</th>
                          <th className="p-3">% of Total</th>
                          <th className="p-3">% Work Done to Contract Value</th>
                          <th className="p-3">% Done to Respective Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evmData[selectedWeek].components?.map((comp: any, idx: number) => (
                          <tr key={idx} className="border-b border-vanilla-custard-50 hover:bg-vanilla-custard-50/50 transition-colors">
                            <td className="p-3 font-medium text-slate-700">{comp.name}</td>
                            <td className="p-3 font-bold text-slate-500">{comp.pctTotal}%</td>
                            <td className="p-3 text-vivid-tangerine-900 font-semibold">
                              {isAdmin && isEditing ? (
                                <input 
                                  value={comp.pctContrib || ''} 
                                  onChange={(e) => {
                                    const newData = {...evmData};
                                    newData[selectedWeek].components[idx].pctContrib = e.target.value.replace(/%/g, '');
                                    setEvmData(newData);
                                  }}
                                  className="w-16 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none"
                                />
                              ) : comp.pctContrib || '0.00'}%
                            </td>
                            <td className="p-3 text-vivid-tangerine-900 font-semibold">
                              {isAdmin && isEditing ? (
                                <input 
                                  value={comp.pctDone || ''} 
                                  onChange={(e) => {
                                    const newData = {...evmData};
                                    newData[selectedWeek].components[idx].pctDone = e.target.value.replace(/%/g, '');
                                    setEvmData(newData);
                                  }}
                                  className="w-16 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none"
                                />
                              ) : comp.pctDone || '0.00'}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="overflow-x-auto bg-white/90 rounded-none border border-vanilla-custard-100 shadow-md hover:shadow-lg transition-all duration-300 self-start">
                    <h3 className="text-xs font-bold text-vivid-tangerine-500 uppercase tracking-widest bg-gradient-to-r from-vanilla-custard-50 to-white p-4 border-b border-vanilla-custard-100">Block Progress</h3>
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-vanilla-custard-200 text-[10px] text-vivid-tangerine-800 uppercase tracking-wider bg-vanilla-custard-50/50">
                          <th className="p-3">Block</th>
                          <th className="p-3">% Done Per Block</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evmData[selectedWeek].blocks?.map((blk: any, idx: number) => (
                          <tr key={idx} className="border-b border-vanilla-custard-50 hover:bg-vanilla-custard-50/50 transition-colors">
                            <td className="p-3 font-medium text-slate-700">{blk.name}</td>
                            <td className="p-3 text-vivid-tangerine-900 font-semibold">
                              {isAdmin && isEditing ? (
                                <input 
                                  value={blk.pctDone || ''} 
                                  onChange={(e) => {
                                    const newData = {...evmData};
                                    newData[selectedWeek].blocks[idx].pctDone = e.target.value.replace(/%/g, '');
                                    setEvmData(newData);
                                  }}
                                  className="w-16 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none"
                                />
                              ) : blk.pctDone || '0.00'}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="lg:col-span-2 flex justify-end mt-4 gap-4">
                    {isAdmin && !isEditing && (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="px-8 py-3 rounded-none font-bold transition-all shadow-md bg-sunflower-gold-500 text-white hover:bg-sunflower-gold-600 active:scale-95"
                      >
                        Edit EVM Data
                      </button>
                    )}
                    {isAdmin && isEditing && (
                      <>
                        <button
                          onClick={() => {
                            setEvmData(JSON.parse(JSON.stringify(originalEvmData)));
                            setIsEditing(false);
                          }}
                          className="px-6 py-3 rounded-none font-bold transition-all bg-vanilla-custard-100 text-slate-500 hover:bg-vanilla-custard-200 active:scale-95"
                        >
                          Discard
                        </button>
                        <button
                          onClick={handleUpdateEVM}
                          disabled={isUpdating || JSON.stringify(evmData[selectedWeek]) === JSON.stringify(originalEvmData?.[selectedWeek])}
                          className={`px-8 py-3 rounded-none font-bold transition-all shadow-md ${isUpdating || JSON.stringify(evmData[selectedWeek]) === JSON.stringify(originalEvmData?.[selectedWeek]) ? 'bg-vanilla-custard-300 text-vanilla-custard-500 cursor-not-allowed' : 'bg-vivid-tangerine-600 text-white hover:bg-vivid-tangerine-700 active:scale-95'}`}
                        >
                          {isUpdating ? 'Updating...' : 'Update EVM Data'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ) : null}
            </div>

          </div>
          </RevealWrapper>
        ) : null}
      </div>

      {/* EVM Update Modal */}
      {showUpdateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm transition-all duration-300">
          <div className="bg-white rounded-none max-w-sm w-full overflow-hidden border shadow-2xl relative flex flex-col text-left p-6 animate-in fade-in zoom-in duration-200">
            <h3 className={`text-lg font-bold mb-2 font-serif ${updateStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
              {updateStatus.includes('✅') ? 'Success!' : 'Error'}
            </h3>
            <p className="text-xs text-vivid-tangerine-800 mb-6 leading-relaxed">
              {updateStatus}
            </p>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setShowUpdateModal(false)}
                className="px-6 py-2.5 bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white font-bold rounded-none text-xs uppercase tracking-wider shadow-md hover:scale-[1.02] active:scale-98 transition-all"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Panel */}
      <footer className="mt-20 border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-left">
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Vektra</p>
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
          <p className="text-[10px] text-vanilla-custard-400 font-bold uppercase tracking-widest">&copy; 2026 Vektra. All Rights Reserved.</p>
        </div>
      </footer>
    </main>
  );
}
