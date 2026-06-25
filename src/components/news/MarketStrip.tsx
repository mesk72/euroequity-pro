'use client'

import { useEffect, useRef, useState } from 'react'

interface IndexQuote {
  name: string
  symbol: string
  price: string
  change: string
  changePct: string
  up: boolean
}

const INDICES = [
  { name: 'DAX',          symbol: 'DAX',   exchange: 'INDEXEURO'     },
  { name: 'CAC 40',       symbol: 'PX1',   exchange: 'INDEXEURO'     },
  { name: 'FTSE MIB',     symbol: 'FTSEMIB', exchange: 'INDEXEURO'   },
  { name: 'FTSE 100',     symbol: 'UKX',   exchange: 'INDEXFTSE'     },
  { name: 'Euro Stoxx 50',symbol: 'SX5E',  exchange: 'INDEXSTOXX'    },
  { name: 'Nikkei 225',   symbol: 'NI225', exchange: 'INDEXNIKKEI'   },
  { name: 'Hang Seng',    symbol: 'HSI',   exchange: 'INDEXHANGSENG' },
  { name: 'ASX 200',      symbol: 'AS51',  exchange: 'INDEXASX'      },
]

async function fetchGoogleFinance(symbol: string, exchange: string): Promise<IndexQuote | null> {
  try {
    const url = `https://www.google.com/finance/quote/${symbol}:${exchange}`
    const r = await fetch(url, { mode: 'no-cors' })
    // no-cors non permette di leggere il body
    return null
  } catch { return null }
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [quotes, setQuotes] = useState<IndexQuote[]>([])

  // TradingView strip per US, commodities, FX
  useEffect(() => {
    if (!tvRef.current) return
    tvRef.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: [
        { proName: 'AMEX:SPY',   title: 'S&P 500'    },
        { proName: 'NASDAQ:QQQ', title: 'Nasdaq 100' },
        { proName: 'AMEX:DIA',   title: 'Dow Jones'  },
        { proName: 'TVC:GOLD',   title: 'Gold'       },
        { proName: 'TVC:USOIL',  title: 'Oil WTI'    },
        { proName: 'TVC:UKOIL',  title: 'Oil Brent'  },
        { proName: 'FX:EURUSD',  title: 'EUR/USD'    },
        { proName: 'FX:USDJPY',  title: 'USD/JPY'    },
        { proName: 'FX:GBPUSD',  title: 'GBP/USD'    },
        { proName: 'FX:USDCHF',  title: 'USD/CHF'    },
      ],
      showSymbolLogo: false,
      isTransparent: true,
      displayMode: 'adaptive',
      colorTheme: 'dark',
      locale: 'en',
    })
    tvRef.current.appendChild(script)
  }, [])

  // Fetch indici EU/Asia da nostra API proxy
  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/api/indices')
        if (!r.ok) return
        const d = await r.json()
        setQuotes(d.quotes || [])
      } catch {}
    }
    load()
    const t = setInterval(load, 60000) // ogni minuto
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      {/* TradingView - US/Commodities/FX */}
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>

      {/* Indici EU/Asia da Google Finance */}
      {quotes.length > 0 && (
        <div style={{ display: 'flex', gap: 16, overflowX: 'auto', padding: '4px 12px', background: 'rgba(0,0,0,0.2)' }}>
          {quotes.map(q => (
            <div key={q.symbol} style={{ flexShrink: 0, textAlign: 'center', minWidth: 80 }}>
              <div style={{ fontSize: 9, color: 'var(--text4)', fontWeight: 700 }}>{q.name}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>
                {q.price}
              </div>
              <div style={{ fontSize: 10, fontWeight: 600, color: q.up ? '#22c55e' : '#ef4444', fontFamily: 'IBM Plex Mono' }}>
                {q.changePct}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        Powered by TradingView & Google Finance · live
      </div>
    </div>
  )
}
