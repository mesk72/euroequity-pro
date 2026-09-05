import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { Analytics } from '@vercel/analytics/react'

export const metadata: Metadata = {
  // ── SITO NON INDICIZZABILE — 5/9/2026, richiesta di Andrea ──
  // ForwardAlpha torna a essere uso personale: nessun dato deve essere
  // visibile a chi non e' autorizzato, ne' sul sito ne' su Google.
  //
  // ATTENZIONE: per RIMUOVERE le pagine gia' indicizzate serve proprio
  // questo tag, e Google deve poterlo LEGGERE. Per questo robots.txt
  // continua a consentire la scansione: bloccarla impedirebbe a Google di
  // vedere il noindex e le pagine resterebbero nell'indice ancora piu' a
  // lungo. La rimozione richiede qualche settimana.
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: { index: false, follow: false, noimageindex: true },
  },

  title: 'ForwardAlpha — Global Equity Research | 7,000+ Stocks Ranked',
  description: 'ForwardAlpha — Institutional-grade Value & Growth scoring across 7,000+ global stocks: Europe, US, Canada, Japan, Hong Kong, Australia. Daily price refresh. Built by ex J.P. Morgan & Zenit SGR Portfolio Manager, CFA.',
  keywords: 'global equity research, stock screening, quantitative analysis, value investing, growth investing, CFA, European stocks, US stocks, Asia Pacific, Japan stocks, Hong Kong stocks, APAC equities, ForwardAlpha',
  authors:     [{ name: 'Andrea Meschini' }],
  openGraph: {
    title:       'ForwardAlpha',
 description: 'Professional global equity research platform',
    type:        'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/flag-icon-css/7.2.3/css/flag-icons.min.css" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-bg text-text antialiased">
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#0d1017',
              color:      '#dde4f0',
              border:     '1px solid #1e2840',
              fontSize:   '13px',
            },
          }}
        />
        {children}
        <Analytics />
      </body>
    </html>
  )
}
