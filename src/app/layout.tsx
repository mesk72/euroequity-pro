import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { Analytics } from '@vercel/analytics/react'

export const metadata: Metadata = {
 title: 'ForwardAlpha — Global Quantitative Equity Research',
 description: 'ForwardAlpha — Proprietary Value & Growth scoring across 2,100+ European and 2,000+ US equities. Daily refresh. Expanding to Canada, Japan and Asia-Pacific within 3 months.',
 keywords: 'global stocks, equity screening, quantitative analysis, value investing, growth investing, CFA, European stocks, US stocks, Asia Pacific',
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
