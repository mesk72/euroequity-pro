'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string
  changePct: string | null
  up: boolean | null
  region: string
}

function IndexBar({ label, quotes, loading }: {
  label: string
  quotes: Quote[]
  loading: boolean
}) {
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '3px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
      <span style={{ fontSize: 9, color: 'var(--text4)', minWidth: 64 }}>{label}</span>
      <span style={{ fontSize: 9, color: 'var(--text4)' }}>Loading...</span>
    </div>
  )

  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '3px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      overflowX: 'auto', flexWrap: 'nowrap', gap: 0 }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text4)',
        letterSpacing: '0.08em', textTransform: 'uppercase',
        minWidth: 64, flexShrink: 0 }}>
        {label}
      </span>
      {quotes.map((q, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center',
          gap: 4, marginRight: 16, flexShrink: 0 }}>
          <span style={{ fontSize: 9, color: 'var(--text4)', fontWeight: 600 }}>
            {q.name}
          </span>
          <span style={{ fontSize: 11, fontWeight: 700,
            color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>
            {q.price}
          </span>
          {q.changePct && (
            <span style={{ fontSize: 10, fontWeight: 600,
              fontFamily: 'IBM Plex Mono',
              color: q.up ? '#22c55e' : '#ef4444' }}>
              {q.changePct}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [quotes, setQuotes] = useState<{ americas: Quote[], europe: Quote[], asia: Quote[] }>({
    americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)

  // Carica indici da Leeway via /api/indices
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const r = await fetch('/api/indices', { cache: 'no-store' })
        if (r.ok) {
          const d = await r.json()
          setQuotes({
            americas: d.americas || [],
            europe:   d.europe   || [],
            asia:     d.asia     || [],
          })
        }
      } catch {}
      setLoading(false)
    }
    load()
    const t = setInterval(load, 900000) // refresh ogni 15 min
    return () => clearInterval(t)
  }, [])

  // TradingView — solo Commodities e FX
  useEffect(() => {
    if (!tvRef.current) return
    tvRef.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: [
        { proName: 'TVC:GOLD',  title: 'Gold'      },
        { proName: 'TVC:USOIL', title: 'Oil WTI'   },
        { proName: 'TVC:UKOIL', title: 'Oil Brent' },
        { proName: 'FX:EURUSD', title: 'EUR/USD'   },
        { proName: 'FX:USDJPY', title: 'USD/JPY'   },
        { proName: 'FX:GBPUSD', title: 'GBP/USD'   },
        { proName: 'FX:USDCHF', title: 'USD/CHF'   },
        { proName: 'FX:USDCAD', title: 'USD/CAD'   },
        { proName: 'FX:AUDUSD', title: 'AUD/USD'   },
      ],
      showSymbolLogo: false,
      isTransparent: true,
      displayMode: 'adaptive',
      colorTheme: 'dark',
      locale: 'en',
    })
    tvRef.current.appendChild(script)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <IndexBar label="Americas" quotes={quotes.americas} loading={loading} />
      <IndexBar label="Europe"   quotes={quotes.europe}   loading={loading} />
      <IndexBar label="Asia Pac" quotes={quotes.asia}     loading={loading} />
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
      <div style={{ fontSize: 8, color: 'var(--text4)', padding: '1px 8px 3px', textAlign: 'right' }}>
        Indices via Leeway · Commodities &amp; FX via TradingView
      </div>
    </div>
  )
}
