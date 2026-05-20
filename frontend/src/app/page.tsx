"use client";
import React from 'react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-950 font-sans">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-br from-vanilla-custard-100/50 to-transparent pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 pt-24 pb-32 relative z-10">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight font-serif bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent py-2">
              Makindu Affordable Housing Project <br/> Report Aggregator
            </h1>
            <p className="text-lg md:text-xl text-vivid-tangerine-800 mb-10 max-w-2xl mx-auto font-medium">
              Transform raw site logs into professional, AI-powered construction reports and predictive analytics.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link 
                href="/dashboard"
                className="px-8 py-3 bg-vivid-tangerine-600 text-white rounded-2xl font-bold text-sm shadow-xl shadow-vivid-tangerine-200 hover:bg-vivid-tangerine-700 hover:scale-[1.02] transition-all"
              >
                Launch Dashboard
              </Link>
              <button className="px-8 py-3 bg-white text-vivid-tangerine-700 border-2 border-vanilla-custard-200 rounded-2xl font-bold text-sm hover:bg-vanilla-custard-50 transition-all">
                Learn More
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-3xl shadow-lg border border-vanilla-custard-100">
            <div className="text-3xl mb-4">📡</div>
            <h3 className="text-lg font-bold mb-2">AI Vision Scan</h3>
            <p className="text-vivid-tangerine-700 text-sm">Automatically extracts data from PDF daily logs with high precision OCR and intelligent parsing.</p>
          </div>
          <div className="bg-white p-6 rounded-3xl shadow-lg border border-vanilla-custard-100">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-lg font-bold mb-2">Trend Analysis</h3>
            <p className="text-vivid-tangerine-700 text-sm">Visualize slippage, labor efficiency, and financial progress across the entire project lifecycle.</p>
          </div>
          <div className="bg-white p-6 rounded-3xl shadow-lg border border-vanilla-custard-100">
            <div className="text-4xl mb-4">📝</div>
            <h3 className="text-lg font-bold mb-2">Smart Generation</h3>
            <p className="text-vivid-tangerine-700 text-sm">Generate executive weekly and monthly reports in Word format, ready for stakeholder review.</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-20 border-t border-vanilla-custard-200 pt-12 pb-8 max-w-7xl mx-auto px-6">
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
              <Link href="/contract" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Contract</Link>
              <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Trends</Link>
            </div>
            <div className="flex justify-center md:justify-end gap-3">
              <Link href="/terms" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-white border border-vanilla-custard-200 px-3 py-1 rounded-full">Terms</Link>
              <Link href="/privacy" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-white border border-vanilla-custard-200 px-3 py-1 rounded-full">Privacy</Link>
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
