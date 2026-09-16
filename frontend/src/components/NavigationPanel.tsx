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

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-vanilla-custard-200 px-3 sm:px-8 py-3 sm:py-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-1.5 sm:gap-4">
          {pathname !== '/' && (
            <Link href="/" className="text-xs font-bold text-vivid-tangerine-950 uppercase tracking-wider bg-white hover:bg-vanilla-custard-50 hover:text-vivid-tangerine-600 border border-vanilla-custard-200 px-2.5 sm:px-4 py-2 rounded-none shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center justify-center">
              Home
            </Link>
          )}
          {pathname !== '/' && pathname !== '/dashboard' && (
            <div className="w-px h-4 bg-vanilla-custard-200"></div>
          )}
          {pathname !== '/dashboard' && pathname !== '/' && (
            <Link href="/dashboard" className="text-xs font-bold text-vivid-tangerine-700 uppercase tracking-wider bg-white hover:bg-vivid-tangerine-50 border border-vivid-tangerine-200/80 px-2.5 sm:px-4 py-2 rounded-none shadow-sm hover:shadow-md transition-all active:scale-[0.98] inline-flex items-center gap-1.5">
              <svg className="w-4 h-4 text-vivid-tangerine-500" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </Link>
          )}
        </div>
        <div className="flex items-center gap-1.5 sm:gap-4">
          {isLoaded && userId && (
            !isAdmin ? (
              <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50/80 border border-amber-200 px-2 sm:px-3.5 py-1.5 sm:py-2 rounded-none shadow-sm hidden sm:inline-block">
                Viewer Access
              </span>
            ) : (
              <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-vivid-tangerine-700 bg-vivid-tangerine-50 border border-vivid-tangerine-200 px-2 sm:px-3.5 py-1.5 sm:py-2 rounded-none shadow-sm hidden sm:inline-block">
                Access
              </span>
            )
          )}
          <UserButton
            afterSignOutUrl="/"
            appearance={{
              elements: {
                avatarBox: "w-8 h-8 sm:w-9 sm:h-9 border border-vivid-tangerine-200/80 rounded-none shadow-md hover:scale-105 transition-transform duration-200",
              }
            }}
          />
        </div>
      </div>
    </nav>
  );
}
