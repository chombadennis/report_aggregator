"use client";
import React from 'react';
import Link from 'next/link';
import { useAuth } from '@clerk/nextjs';

export default function Footer() {
  const { isLoaded, userId } = useAuth();

  return (
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
            {isLoaded && userId && (
              <>
                <Link href="/contract" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Contract</Link>
                <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Trends</Link>
                <Link href="/variance-tracker" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Schedule Variance</Link>
              </>
            )}
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
  );
}
