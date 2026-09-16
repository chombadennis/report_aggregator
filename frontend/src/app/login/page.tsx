"use client";
import React, { useState, useEffect } from "react";
import { SignIn } from "@clerk/nextjs";
import Link from "next/link";
import RevealWrapper from "@/components/animations/RevealWrapper";

export default function LoginPage() {
  const [redirectUrl, setRedirectUrl] = useState("/dashboard");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const redir = params.get("redirect") || params.get("redirect_url");
      if (redir) {
        setRedirectUrl(redir);
      }
    }
  }, []);

  return (
    <main className="relative min-h-screen flex flex-col justify-center items-center px-4 py-8 sm:py-0 overflow-y-auto bg-slate-950">
      {/* Background Glowing Orbs */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-sunflower-gold-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 rounded-full bg-vivid-tangerine-500/10 blur-3xl pointer-events-none" />

      {/* Decorative Grid Lines */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Branded Logo and Title Header */}
      <div className="relative z-10 text-center mb-4 sm:mb-8 max-w-md animate-fade-in">
        <Link href="/" className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-all mb-4">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5 text-vivid-tangerine-400">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
          <span className="text-[10px] font-black uppercase text-vivid-tangerine-300 tracking-wider">Back to Home</span>
        </Link>
        <h1 className="text-3xl font-black font-serif text-white tracking-tight leading-none mb-2">
          Vektra <span className="bg-gradient-to-r from-sunflower-gold-400 to-vivid-tangerine-500 bg-clip-text text-transparent"></span>
        </h1>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          Field Reporting &amp; Analytics Portal
        </p>
      </div>

      {/* Glassmorphic Container for Clerk SignIn */}
      <RevealWrapper direction="up">
        <div className="relative z-10 w-full max-w-[440px] rounded-none p-1 bg-gradient-to-br from-white/10 via-white/5 to-white/0 shadow-2xl backdrop-blur-xl border border-white/10">
          <div className="bg-slate-900/60 rounded-none overflow-hidden flex flex-col justify-center items-center py-4 sm:py-6 px-3 sm:px-4">
          <SignIn
            routing="hash"
            afterSignInUrl={redirectUrl}
            afterSignUpUrl={redirectUrl}
            appearance={{
              variables: {
                colorPrimary: "#ff8400", // vivid-tangerine-500
                colorBackground: "#1e293b", // slate-800
                colorText: "#ffffff",
                colorTextSecondary: "#94a3b8", // slate-400
                colorInputBackground: "#0f172a", // slate-900
                colorInputText: "#ffffff",
              },
              elements: {
                card: "bg-transparent shadow-none w-full border-none",
                headerTitle: "text-white text-xl font-bold font-serif",
                headerSubtitle: "text-slate-400 text-xs",
                socialButtonsBlockButton: "border border-slate-700 bg-slate-800 hover:bg-slate-700 text-white transition-all rounded-none",
                formButtonPrimary: "bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 hover:opacity-95 text-white font-bold text-sm py-2.5 rounded-none transition-all shadow-lg shadow-vivid-tangerine-500/20 border-none",
                formFieldLabel: "text-slate-300 text-xs font-semibold mb-1",
                formFieldInput: "bg-slate-950 border border-slate-700 focus:border-vivid-tangerine-500 focus:ring-1 focus:ring-vivid-tangerine-500 rounded-none py-2 px-3 text-sm text-white placeholder-slate-600 transition-all",
                footerActionText: "text-slate-400 text-xs",
                footerActionLink: "text-vivid-tangerine-400 hover:text-vivid-tangerine-300 font-bold transition-colors",
                identityPreviewText: "text-white",
                identityPreviewEditButtonIcon: "text-vivid-tangerine-400",
                formFieldAction: "text-vivid-tangerine-400 hover:text-vivid-tangerine-300 transition-colors"
              }
            }}
          />
        </div>
      </div>
      </RevealWrapper>

      <div className="relative z-10 mt-4 sm:mt-8 text-center">
        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
          Secured with Clerk &amp; Cryptographic Signatures
        </p>
      </div>
    </main>
  );
}
