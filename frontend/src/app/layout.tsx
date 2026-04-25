import type { Metadata } from "next";
import { Inter, Outfit } from 'next/font/google'
import "./globals.css";

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })
const outfit = Outfit({ subsets: ['latin'], variable: '--font-display' })

export const metadata: Metadata = {
  title: 'ContractEnv — AI Contract Negotiation',
  description: 'Two AI agents negotiate your business contract. Private constraints, live streaming, autonomous agreement.',
  openGraph: { 
    title: 'ContractEnv — AI Contract Negotiation', 
    description: 'Two AI agents negotiate your business contract.', 
    type: 'website' 
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body className="font-sans antialiased bg-slate-50 text-slate-900 selection:bg-pink-200 selection:text-pink-900">
        <div className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
