'use client'

import { useEffect, useRef, useState } from 'react'

interface IndexQuote {
  name: string
  price: string
  changePct: string
  up: boolean
}

// Google Finance ha un endpoint JSON non documentato ma pubblico
// https://www.google.com/finance/quote/DAX:INDEXEURO
// Usa l'API search di Google Finance che restituisce JSON
const GOOGLE_INDICES = [
  { name: 'DAX',            query: 'DAX:INDEXEURO'        },
  { name: 'CAC 40',         query: 'PX1:INDEXEURO'        },
  { name: 'FTSE MIB',       query: 'FTSEMIB:INDEXEURO'    },
  { name: 'FTSE 100',       query: 'UKX:INDEXFTSE'        },
  { name: 'Euro Stoxx 50',  query: 'SX5E:INDEXSTOXX'      },
  { name: 'Nikkei 225',     query: 'NI225:INDEXNIKKEI'    },
  { name: 'Hang Seng',      query: 'HSI:INDEXHANGSENG'    },
  { name: 'ASX 200',        query: 'AS51:INDEXASX'        },
]

async function fetchGoogleIndex(query: string): Promise<{ price: string; changePct: string; up: boolean } | null> {
  try {
    // Google Finance JSON endpoint - funziona dal browser
    const url = 'https://www.google.com/finance/quote/' + query
    const r = await fetch(url, {
      headers: { 'Accept': 'text/html' },
      mode: 'cors',
    })
    if (!r.ok) return null
    const html = await r.text()
    // Estrai prezzo e variazione dal HTML
    const priceMatch = html.match(/data-last-price="([^"]+)"/)
    const changeMatch = html.match(/data-last-price-change-percent="([^"]+)"/)
    if (!priceMatch) return null
    const price = parseFloat(priceMatch[1])
    const changePct = changeMatch ? parseFloat(changeMatch[1]) * 100 : 0
    return {
      price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%',
      up: changePct >= 0,
    }
  } catch { return null }
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [quotes, setQuotes] = useState<(IndexQuote | null)[]>([])

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

  useEffect(() => {
    const load = async () => {
      const results = await Promise.all(
        GOOGLE_INDICES.map(async ({ name, query }) => {
          const q = await fetchGoogleIndex(query)
          if (!q) return null
          return { name, ...q }
        })
      )
      setQuotes(results)
    }
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [])

  const validQuotes = quotes.filter(Boolean) as IndexQuote[]

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
      {validQuotes.length > 0 && (
        <div style={{ display: 'flex', gap: 16, overflowX: 'auto', padding: '4px 12px', background: 'rgba(0,0,0,0.15)' }}>
          {validQuotes.map((q, i) => (
            <div key={i} style={{ flexShrink: 0, textAlign: 'center', minWidth: 75 }}>
              <div style={{ fontSize: 9, color: 'var(--text4)', fontWeight: 700 }}>{q.name}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>{q.price}</div>
              <div style={{ fontSize: 10, fontWeight: 600, color: q.up ? '#22c55e' : '#ef4444', fontFamily: 'IBM Plex Mono' }}>{q.changePct}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        TradingView (US/Commodities/FX) · Google Finance (EU/Asia) · live
      </div>
    </div>
  )
}
