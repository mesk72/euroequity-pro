'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string
  changePct: string
  up: boolean
}

const INDICES = [
  { name: 'DAX',           sym: '%5EGDAXI'   },
  { name: 'CAC 40',        sym: '%5EFCHI'    },
  { name: 'FTSE MIB',      sym: 'FTSEMIB.MI' },
  { name: 'FTSE 100',      sym: '%5EFTSE'    },
  { name: 'Euro Stoxx 50', sym: '%5ESTOXX50E'},
  { name: 'Nikkei 225',    sym: '%5EN225'    },
  { name: 'Hang Seng',     sym: '%5EHSI'     },
  { name: 'ASX 200',       sym: '%5EAXJO'    },
]

async function fetchIndexPrice(sym: string): Promise<{ price: number; changePct: number } | null> {
  try {
    // Usa rss2json per bypassare CORS - stessa tecnica delle notizie
    const yahooUrl = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=' + sym + '&region=US&lang=en-US'
    const api = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(yahooUrl)
    const r = await fetch(api)
    if (!r.ok) return null
    const d = await r.json()
    // Il feed RSS di Yahoo Finance include il prezzo nel titolo o description
    // es: "DAX 18,234.56 +1.23%"
    if (d.status === 'ok' && d.feed) {
      const title = d.feed.title || ''
      // Prova a estrarre prezzo dalla descrizione del feed
      const desc = d.feed.description || ''
      const priceMatch = (title + ' ' + desc).match(/([\d,]+\.?\d*)\s*([\+\-]\d+\.?\d*%?)/)
      if (priceMatch) {
        const price = parseFloat(priceMatch[1].replace(/,/g, ''))
        return { price, changePct: 0 }
      }
    }
    return null
  } catch { return null }
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [quotes, setQuotes] = useState<Quote[]>([])

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

  // Fetch prezzi indici via /api/indices (server-side proxy)
  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/api/indices', { cache: 'no-store' })
        if (!r.ok) return
        const d = await r.json()
        if (d.quotes?.length > 0) setQuotes(d.quotes)
      } catch {}
    }
    load()
    const t = setInterval(load, 900000) // ogni 15 minuti
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
        TradingView (US/Commodities/FX) · Yahoo Finance (EU/Asia) · updates every minute
      </div>
    </div>
  )
}
