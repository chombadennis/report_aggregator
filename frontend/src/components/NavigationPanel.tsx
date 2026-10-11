"use client";
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUser, useAuth, UserButton } from '@clerk/nextjs';

export default function NavigationPanel() {
  const { isLoaded, userId } = useAuth();
  const { user } = useUser();
  const pathname = usePathname();
  const userEmail = user?.primaryEmailAddress?.emailAddress;
  const adminEmail = process.env.NEXT_PUBLIC_ADMIN_EMAIL || '';
  const isAdmin = userEmail && adminEmail && userEmail.toLowerCase() === adminEmail.toLowerCase();

  const navItems = [
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Contracts', href: '/contract' },
    { name: 'Trends', href: '/trends' },
    { name: 'Schedule Variance', href: '/variance-tracker' },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-stone-200/70 shadow-[0_1px_3px_rgba(0,0,0,0.02)] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-3">
        
        {/* Left Side: Brand & Quick Back */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <Link
            href="/"
            className="group flex items-center gap-2 text-stone-900 transition-opacity hover:opacity-90"
            title="Go to Home"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-sunflower-gold-500 to-vivid-tangerine-500 flex items-center justify-center text-white shadow-sm shadow-vivid-tangerine-500/20 group-hover:scale-105 transition-transform duration-200">
              <span className="font-serif font-black text-xs tracking-tight">V</span>
            </div>
            <span className="font-serif font-bold text-sm bg-gradient-to-r from-stone-900 to-stone-700 bg-clip-text text-transparent hidden sm:inline-block">
              Vektra
            </span>
          </Link>

          {pathname !== '/' && pathname !== '/dashboard' && (
            <>
              <span className="text-stone-300 text-xs hidden sm:inline">/</span>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-stone-600 hover:text-vivid-tangerine-600 hover:bg-stone-100/70 rounded-md transition-colors duration-150"
              >
                <svg className="w-3.5 h-3.5 text-stone-400 group-hover:text-vivid-tangerine-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
                <span>Dashboard</span>
              </Link>
            </>
          )}
        </div>

        {/* Center: Sleek Segmented Navigation Pills */}
        {isLoaded && userId && (
          <div className="flex items-center gap-1 p-1 bg-stone-100/80 rounded-full border border-stone-200/60 overflow-x-auto no-scrollbar max-w-full">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 whitespace-nowrap ${
                    isActive
                      ? 'bg-white text-vivid-tangerine-700 font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.06)] border border-stone-200/50'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-white/60'
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </div>
        )}

        {/* Right Side: Role Badge & Profile */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {isLoaded && userId && (
            !isAdmin ? (
              <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200/70 shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                Viewer
              </span>
            ) : (
              <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-vivid-tangerine-50 text-vivid-tangerine-700 border border-vivid-tangerine-200/70 shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-vivid-tangerine-500" />
                Access
              </span>
            )
          )}
          
          <UserButton
            afterSignOutUrl="/"
            appearance={{
              elements: {
                avatarBox: "w-7 h-7 sm:w-8 sm:h-8 rounded-full ring-2 ring-stone-200/80 hover:ring-vivid-tangerine-400 transition-all duration-200 shadow-sm",
              }
            }}
          />
        </div>
      </div>
    </nav>
  );
}
