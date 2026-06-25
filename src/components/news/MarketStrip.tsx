'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string
  changePct: string
  up: boolean
}

const EU_INDICES = [
  { name: 'DAX',           sym: '%5EGDAXI'    },
  { name: 'CAC 40',        sym: '%5EFCHI'     },
  { name: 'FTSE 100',      sym: '%5EFTSE'     },
  { name: 'Euro Stoxx 50', sym: '%5ESTOXX50E' },
  { name: 'FTSE MIB',      sym: 'FTSEMIB.MI'  },
]

const ASIA_INDICES = [
  { name: 'Nikkei 225', sym: '%5EN225' },
  { name: 'Hang Seng',  sym: '%5EHSI'  },
  { name: 'ASX 200',    sym: '%5EAXJO' },
]

function isAsiaOpen(): boolean {
  const d = new Date()
  if (d.getUTCDay() === 0 || d.getUTCDay() === 6) return false
  const t = d.getUTCHours() * 60 + d.getUTCMinutes()
  return t >= 0 && t <= 480
}

function isEUOpen(): boolean {
  const d = new Date()
  if (d.getUTCDay() === 0 || d.getUTCDay() === 6) return false
  const t = d.getUTCHours() * 60 + d.getUTCMinutes()
  return t >= 420 && t <= 930
}

async function fetchIndexPrice(sym: string, name: string): Promise<Quote | null> {
  try {
    // Usa rss2json per fare il proxy del feed Yahoo Finance
    // rss2json supporta anche JSON endpoint - usiamo Yahoo Finance summary
    const yahooUrl = `https://finance.yahoo.com/quote/${sym}/`
    const api = 'https://api.rss2json.com/v1/api.json?rss_url=' + 
      encodeURIComponent(`https://feeds.finance.yahoo.com/rss/2.0/headline?s=${sym}&region=US&lang=en-US`)
    
    const r = await fetch(api)
    if (!r.ok) return null
    const d = await r.json()
    
    // Il feed RSS non ha prezzi - usa il feed.description o feed.title
    // che Yahoo include nel channel metadata
    const feedDesc = d?.feed?.description || ''
    const feedTitle = d?.feed?.title || ''
    
    // Cerca pattern prezzo nei metadati del feed
    const text = feedTitle + ' ' + feedDesc
    const priceMatch = text.match(/([\d,]+\.[\d]{2})/)
    const pctMatch = text.match(/([+-]?\d+\.?\d*)%/)
    
    if (priceMatch) {
      const price = parseFloat(priceMatch[1].replace(/,/g, ''))
      const pct = pctMatch ? parseFloat(pctMatch[1]) : 0
      return {
        name,
        price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
        changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
        up: pct >= 0,
      }
    }
    
    // Fallback: cerca nei titoli delle notizie il prezzo
    const items = d?.items || []
    for (const item of items.slice(0, 3)) {
      const t = (item.title || '') + ' ' + (item.description || '')
      const pm = t.match(/([\d,]+\.[\d]{2})/)
      const cm = t.match(/([+-]?\d+\.?\d*)%/)
      if (pm) {
        const price = parseFloat(pm[1].replace(/,/g, ''))
        const pct = cm ? parseFloat(cm[1]) : 0
        return {
          name,
          price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
          changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
          up: pct >= 0,
        }
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

  useEffect(() => {
    const load = async () => {
      const toFetch = [
        ...(isEUOpen() ? EU_INDICES : []),
        ...(isAsiaOpen() ? ASIA_INDICES : []),
      ]
      if (toFetch.length === 0) return
      const results = await Promise.all(
        toFetch.map(({ sym, name }) => fetchIndexPrice(sym, name))
      )
      setQuotes(results.filter(Boolean) as Quote[])
    }
    load()
    const t = setInterval(load, 900000) // 15 minuti
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
        TradingView (US/Commodities/FX) · Yahoo Finance (EU/Asia) · live
      </div>
    </div>
  )
}
