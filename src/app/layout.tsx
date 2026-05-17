import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title:       'EuroEquity Pro — European Equity Research',
  description: 'Professional European equity screening and research platform. Real data for Borsa Italiana, DAX, CAC 40 and all major Eurozone markets.',
  keywords:    'European stocks, Borsa Italiana, equity screening, fundamental analysis, CFA',
  authors:     [{ name: 'Andrea Meschini' }],
  openGraph: {
    title:       'EuroEquity Pro',
    description: 'Professional European equity research platform',
    type:        'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
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
      </body>
    </html>
  )
}
