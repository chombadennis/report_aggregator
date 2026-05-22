"use client";
import React from 'react';
import Link from 'next/link';

export default function TermsPage() {
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
                Terms & Conditions
              </h1>
              <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-widest mt-1">
                NeuralAxis Labs Platform Agreement
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
              Welcome to the Makindu Affordable Housing Project Report Aggregator. This internal platform is designed purely for knowledge sharing, site progress analysis, checking, and tracking. It does not constitute or replace official reporting, nor does it represent a consultancy service or establish any contractual relationship with the client, project contractors, or consultants. By accessing or using this system, you agree to comply with and be bound by the following Terms and Conditions.
            </p>
          </div>

          <div className="border-t border-vanilla-custard-100 my-6" />

          {/* Section 1 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">1.</span> License and System Usage
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Authorized internal team members are granted a non-exclusive, non-transferable, revocable license to access and use the Report Aggregator solely for internal site progress analysis, tracking, and information checking purposes.
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              You agree not to modify, reverse engineer, decompile, or attempt to extract the source code or proprietary analytics frameworks of the platform.
            </p>
          </div>

          {/* Section 2 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">2.</span> Intellectual Property & Branding
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              All software modules, analytical models, UI/UX designs, and technical architectures are the proprietary assets of the developers.
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              All uploaded site logs, correspondence, and tracking records remain private and are used solely for the internal site analysis.
            </p>
          </div>

          {/* Section 3 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">3.</span> AI Output Accuracy and Professional Judgment
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              This system uses advanced language and analytical models to process uploaded site records and assist in internal progress checking. While these analytical outputs are highly detailed, they are intended solely for informational reference and internal knowledge.
            </p>
            <p className="text-xs text-red-600 font-bold bg-red-50 p-4 rounded-2xl border border-red-100">
              IMPORTANT: AI and automated analytics insights are purely for internal information checking and do not constitute professional advice, direct physical inspection, certified quantity surveys, or qualified legal counsel. This platform is not for official reporting, and outputs must not be used for official dissemination or contractual claims.
            </p>
          </div>

          {/* Section 4 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">4.</span> Document Integrity & Cache Management
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Users are responsible for the accuracy of their uploaded information. Deleting a record from the register permanently removes all associated files and processed tracking data from the platform. We are not responsible for any data loss resulting from user deletion actions.
            </p>
          </div>

          {/* Section 5 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">5.</span> Service Interruption and Maintenance
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Transient service interruptions or slowdowns may occur due to third-party API availability, network conditions, or periodic system updates. Regular maintenance is performed to ensure the system remains available for tracking needs.
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
                <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
                <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
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
