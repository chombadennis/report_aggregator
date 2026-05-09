"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function ContractSummary() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const resp = await fetch('http://localhost:8000/api/contract-summary');
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

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-900 p-8">
      <div className="max-w-4xl mx-auto">
        <Link href="/" className="text-vivid-tangerine-600 hover:underline mb-8 inline-block font-bold">← Back to Dashboard</Link>
        
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
    </main>
  );
}
