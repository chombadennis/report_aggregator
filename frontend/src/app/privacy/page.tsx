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
              NeuralAxis Labs developed the Makindu Affordable Housing Project Report Aggregator to provide professional, visual, and AI-enabled construction reporting tools. We take data security and privacy seriously. This Privacy Policy details how we handle, process, and secure project documents, logs, and sensitive information.
            </p>
          </div>

          <div className="border-t border-vanilla-custard-100 my-6" />

          {/* Section 1 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">1.</span> Types of Data We Process
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              We process only standard project documents uploaded directly by authorized site managers and consultants:
            </p>
            <ul className="list-disc list-inside text-xs text-vivid-tangerine-800 space-y-1.5 pl-2">
              <li>Site Daily and Weekly Reports (e.g. materials lists, labor statistics, weather comments).</li>
              <li>Official Project Correspondence (e.g. contractor letters, client instructions, meeting minutes).</li>
              <li>Contract Summaries (e.g. commencement dates, contract periods, planned milestones).</li>
            </ul>
          </div>

          {/* Section 2 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">2.</span> How Data is Processed & AI Processing
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              When a document is uploaded, it is sent securely to the NeuralAxis Labs integrated AI engine, which calls the Vertex AI API (Gemini 2.5 Flash and Pro models).
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed font-bold bg-vanilla-custard-50 p-3.5 rounded-xl border border-vanilla-custard-150">
              🔒 Zero Data Training Guarantee: All Vertex AI calls are securely routed under enterprise data privacy terms. Respective LLM models DO NOT train on, retain, or store your project correspondence, site logs, or financial data for public model improvements.
            </p>
          </div>

          {/* Section 3 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">3.</span> Storage and Cache Integrity
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              Uploaded files are stored locally in the secure project environment inside the `cache` directory. These files are processed locally on the project server and are not shared with any third-party websites or marketing vendors.
            </p>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              As a user, you retain complete authority over your cached data. Using the <strong>Delete Document</strong> button on the dashboard register completely removes all files, OCR metadata, and analysis JSONs from our systems.
            </p>
          </div>

          {/* Section 4 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">4.</span> Security Safeguards
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              NeuralAxis Labs implements advanced logical security practices to safeguard project records:
            </p>
            <ul className="list-disc list-inside text-xs text-vivid-tangerine-800 space-y-1.5 pl-2">
              <li>Encrypted transit of API communication between the frontend, backend, and GCP model endpoints.</li>
              <li>Secure sandboxed cache folders for storing temporary uploads and processing page visual slices.</li>
              <li>Regular maintenance sweeps to ensure that no orphan files or un-cleared mock assets reside on disk.</li>
            </ul>
          </div>

          {/* Section 5 */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-vivid-tangerine-950 font-serif flex items-center gap-2">
              <span className="text-sunflower-gold-500">5.</span> Policy Modifications
            </h3>
            <p className="text-xs text-vivid-tangerine-800 leading-relaxed">
              NeuralAxis Labs reserves the right to update this policy as technical modules, API versions, and safety frameworks are upgraded. We will always date revisions at the top of the policy page.
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
