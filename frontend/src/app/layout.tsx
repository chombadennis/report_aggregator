import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AHP Report Aggregator",
  description: "Automated Construction Reporting",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
