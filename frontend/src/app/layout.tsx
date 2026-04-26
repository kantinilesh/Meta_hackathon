import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="en">
      <body className="font-sans antialiased bg-slate-50 text-slate-900 selection:bg-pink-200 selection:text-pink-900">
        <div className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
