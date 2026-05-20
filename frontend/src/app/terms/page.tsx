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
              Welcome to the Makindu Affordable Housing Project Report Aggregator. By accessing or using this system, you agree to comply with and be bound by the following Terms and Conditions. These terms govern the relationship between you (the "User"), NeuralAxis Labs ("Developer"), and the Makindu Affordable Housing Project.
            </p>
          </div>

          <div className="border-t border-vanilla-custard-100 my-6" />

          {/* Section 1 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">1.</span> License and System Usage
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              NeuralAxis Labs grants the authorized project management and consulting teams of the Makindu Affordable Housing Project a non-exclusive, non-transferable, revocable license to access and use the Report Aggregator solely for official construction monitoring, claims analysis, and stakeholder reporting purposes. 
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              You agree not to modify, reverse engineer, decompile, or attempt to extract the source code of the AI Vision engines or parsing frameworks without explicit written consent from NeuralAxis Labs.
            </p>
          </div>

          {/* Section 2 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">2.</span> Intellectual Property & Branding
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              All software modules, machine learning models, UI/UX designs, logo trademarks, and technical architectures are the exclusive intellectual property of <strong>NeuralAxis Labs</strong>. 
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              All project correspondence, uploaded site daily/weekly logs, contract briefs, and aggregated reporting results remain the exclusive property of the Makindu Affordable Housing Project partners and respective contractors.
            </p>
          </div>

          {/* Section 3 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">3.</span> AI Output Accuracy and Professional Judgment
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              This system uses state-of-the-art visual Large Language Models (Gemini 2.5 Flash and Pro) developed under premium integrations by NeuralAxis Labs to perform OCR and extract contractual risks/action items. While highly precise, AI outputs are intended solely for decision support.
            </p>
            <p className="text-xs text-red-600 font-bold bg-red-50 p-4 rounded-2xl border border-red-100">
              IMPORTANT: Artificial intelligence and automated parsing insights are not a substitute for direct physical inspection, certified quantity surveys, or qualified legal counsel regarding Extensions of Time (EOT) and liquidated damages. All aggregated metrics must be reviewed and certified by the Lead Consultant or Project Manager before official dissemination.
            </p>
          </div>

          {/* Section 4 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">4.</span> Document Integrity & Cache Management
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Users are solely responsible for verifying the accuracy of uploaded files. Deleting an uploaded correspondence or site report from the register permanently wipes its associated parsed metadata, PDF files, and visual OCR snapshots from the server cache. NeuralAxis Labs is not responsible for data loss due to user-initiated deletion actions.
            </p>
          </div>

          {/* Section 5 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">5.</span> Service Interruption and Maintenance
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              While NeuralAxis Labs maintains a 99.9% uptime target, transient service interruptions may occur due to external AI cloud API limits, rate limiting (429 mitigation blocks), or standard platform updates. We carry out regular optimizations to ensure minimal disruption to critical reporting pipelines.
            </p>
          </div>

        </div>

        {/* Footer */}
        <footer className="mt-12 border-t border-vanilla-custard-200 pt-8 pb-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-left text-xs font-semibold text-vivid-tangerine-400 uppercase tracking-wider">
            &copy; 2026 Makindu Affordable Housing Project
          </div>
          
          <div className="flex items-center gap-2.5">
            <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
            <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
            <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
          </div>
        </footer>
      </div>
    </main>
  );
}
