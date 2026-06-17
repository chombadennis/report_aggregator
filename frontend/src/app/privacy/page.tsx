"use client";
import React from 'react';
import Link from 'next/link';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-950 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 border-b border-vanilla-custard-200 pb-6">
          <div className="flex items-center gap-4">
            <Link href="/" className="hover:scale-105 transition-transform">
              <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-10 w-10 rounded-full aspect-square object-cover shadow-sm" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif leading-none">
                Privacy Policy
              </h1>
              <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-widest mt-1">
                Data Security and Privacy Standards
              </p>
            </div>
          </div>
          <Link href="/dashboard" className="text-[10px] font-black text-white bg-vivid-tangerine-600 uppercase tracking-widest px-4 py-2 rounded-full hover:bg-vivid-tangerine-700 transition-colors shadow-md">
            ← Dashboard
          </Link>
        </div>

        {/* Content Container */}
        <div className="bg-white p-8 md:p-12 rounded-3xl shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200 text-left space-y-8">
          
          <div>
            <p className="text-xs text-vivid-tangerine-500 font-bold uppercase tracking-wider mb-2">Effective Date: May 20, 2026</p>
            <p className="text-sm text-vivid-tangerine-800 leading-relaxed font-medium">
              The Makindu Affordable Housing Project Report Aggregator is an internal platform developed for knowledge sharing, site progress tracking, checking, and internal analysis. This is not an official reporting service, nor does it constitute any consultancy service or formal contract with the client, project contractors, or consultants. This Privacy Policy details how we handle, process, and secure project documents, logs, and internal site information.
            </p>
          </div>

          <div className="border-t border-vanilla-custard-100 my-6" />

          {/* Section 1 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">1.</span> Types of Data We Process
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              We process standard project documents uploaded solely for internal tracking and analysis purposes:
            </p>
            <ul className="list-disc list-inside text-xs text-vivid-tangerine-800 space-y-1.5 pl-2">
              <li>Site Daily and Weekly Logs (e.g. materials lists, labor statistics, weather comments) to monitor site progress.</li>
              <li>Project correspondence (e.g. contractor letters, client instructions, meeting minutes) uploaded solely for internal awareness and action checking.</li>
              <li>Contract summaries (e.g. commencement dates, contract periods, planned milestones) for internal alignment.</li>
            </ul>
          </div>

          {/* Section 2 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">2.</span> How Data is Processed & AI Processing
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              When a document is uploaded, it is processed securely using our integrated AI and analytics engine to extract key updates and tracking points.
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed font-bold bg-vanilla-custard-50 p-3.5 rounded-xl border border-vanilla-custard-150">
              🔒 Zero Data Training Guarantee: All processing is conducted securely under enterprise data privacy standards. The AI models used do not train on, retain, or store your uploaded project files, site logs, or financial tracking data for public or external model improvements.
            </p>
          </div>

          {/* Section 3 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">3.</span> Storage and Cache Integrity
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Uploaded files are temporarily stored and processed within a secure project environment. These files are processed solely for internal tracking purposes and are not shared with any third-party websites or marketing vendors.
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              As a user, you retain complete control over your uploaded data. Using the <strong>Delete Document</strong> button on the dashboard register completely removes all files and related processed records from the platform.
            </p>
          </div>

          {/* Section 4 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">4.</span> Security Safeguards
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Advanced logical security practices are implemented to safeguard all internal records:
            </p>
            <ul className="list-disc list-inside text-xs text-vivid-tangerine-800 space-y-1.5 pl-2">
              <li>Encrypted transit of all data communication within the platform environment.</li>
              <li>Secure sandboxed environments for storing and processing temporary uploads.</li>
              <li>Regular system maintenance to ensure prompt removal of temporary files.</li>
            </ul>
          </div>

          {/* Section 5 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">5.</span> Policy Modifications
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              We reserve the right to update this policy as technical and analytical modules are upgraded. We will always date revisions at the top of the policy page.
            </p>
          </div>

        </div>

        {/* Footer */}
        <footer className="border-t border-vanilla-custard-200 pt-12 pb-8 mt-16 w-full text-left">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8">
            <div>
              <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
              <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4">Field Intelligence &amp; Reporting</p>
              <div className="flex items-center gap-2.5">
                <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
                <a href="https://neuralaxislabs.online" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                  <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
                  <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
                </a>
              </div>
            </div>
            <div className="flex flex-col items-start md:items-end gap-4">
              <div className="flex gap-5 flex-wrap">
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
      </div>
    </main>
  );
}
