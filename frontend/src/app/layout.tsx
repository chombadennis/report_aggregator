import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource-variable/lexend";
import "@fontsource/lora";
import "@fontsource/merriweather";
import "./globals.css";

export const metadata: Metadata = {
  title: "Construction Report Aggregator",
  description: "Professional aggregation system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
