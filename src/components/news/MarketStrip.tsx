'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string
  changePct: string
  up: boolean
}

const INDICES = [
  { name: 'DAX',           symbol: '%5EGDAXI' },
  { name: 'CAC 40',        symbol: '%5EFCHI'  },
  { name: 'FTSE MIB',      symbol: 'FTSEMIB.MI' },
  { name: 'FTSE 100',      symbol: '%5EFTSE'  },
  { name: 'Euro Stoxx 50', symbol: '%5ESTOXX50E' },
  { name: 'Nikkei 225',    symbol: '%5EN225'  },
  { name: 'Hang Seng',     symbol: '%5EHSI'   },
  { name: 'ASX 200',       symbol: '%5EAXJO'  },
]

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [quotes, setQuotes] = useState<Quote[]>([])

  // TradingView - US/Commodities/FX
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

  // Yahoo Finance dal browser - EU/Asia indices
  useEffect(() => {
    const load = async () => {
      try {
        const syms = INDICES.map(i => i.symbol).join(',')
        const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${syms}&fields=regularMarketPrice,regularMarketChangePercent`
        const r = await fetch(url, {
          headers: {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
          },
          mode: 'cors',
        })
        if (!r.ok) return
        const d = await r.json()
        const results = d?.quoteResponse?.result || []
        const q: Quote[] = INDICES.map(idx => {
          const decoded = decodeURIComponent(idx.symbol)
          const found = results.find((r: any) =>
            r.symbol === decoded || r.symbol === idx.symbol.replace(/%5E/g, '^')
          )
          if (!found) return null
          const pct = found.regularMarketChangePercent
          return {
            name: idx.name,
            price: found.regularMarketPrice?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '-',
            changePct: pct != null ? (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%' : '-',
            up: pct >= 0,
          }
        }).filter(Boolean) as Quote[]
        if (q.length > 0) setQuotes(q)
      } catch {}
    }
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
      {quotes.length > 0 && (
        <div style={{ display: 'flex', gap: 16, overflowX: 'auto', padding: '5px 12px', background: 'rgba(0,0,0,0.15)' }}>
          {quotes.map((q, i) => (
            <div key={i} style={{ flexShrink: 0, textAlign: 'center', minWidth: 80 }}>
              <div style={{ fontSize: 9, color: 'var(--text4)', fontWeight: 700 }}>{q.name}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>{q.price}</div>
              <div style={{ fontSize: 10, fontWeight: 600, fontFamily: 'IBM Plex Mono', color: q.up ? '#22c55e' : '#ef4444' }}>{q.changePct}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        TradingView (US/Commodities/FX) · Yahoo Finance (EU/Asia indices) · live
      </div>
    </div>
  )
}
