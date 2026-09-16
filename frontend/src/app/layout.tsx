import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "@fontsource-variable/inter";
import "@fontsource-variable/lexend";
import "@fontsource/lora";
import "@fontsource/merriweather";
import "./globals.css";

import CustomCursor from "@/components/CustomCursor";

export const metadata: Metadata = {
  title: "Construction Report Aggregator",
  description: "Professional aggregation system",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="antialiased">
          <CustomCursor />
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
