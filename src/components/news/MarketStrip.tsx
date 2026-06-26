'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string | null
  changePct: string | null
  up: boolean | null
}

function IndexBar({ label, quotes, loading }: {
  label: string; quotes: Quote[]; loading: boolean
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '3px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      overflowX: 'auto', flexWrap: 'nowrap', gap: 0 }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text4)',
        letterSpacing: '0.08em', textTransform: 'uppercase',
        minWidth: 64, flexShrink: 0 }}>
        {label}
      </span>
      {loading ? (
        <span style={{ fontSize: 9, color: 'var(--text4)' }}>—</span>
      ) : quotes.length === 0 ? (
        <span style={{ fontSize: 9, color: 'var(--text4)' }}>No data</span>
      ) : quotes.map((q, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center',
          gap: 4, marginRight: 16, flexShrink: 0 }}>
          <span style={{ fontSize: 9, color: 'var(--text4)', fontWeight: 600 }}>
            {q.name}
          </span>
          <span style={{ fontSize: 11, fontWeight: 700,
            color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>
            {q.price ?? '—'}
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
  const [quotes, setQuotes] = useState<{ americas: Quote[]; europe: Quote[]; asia: Quote[] }>({
    americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/indices')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d) setQuotes({ americas: d.americas || [], europe: d.europe || [], asia: d.asia || [] })
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

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
        Indices updated daily via Leeway · Commodities &amp; FX live via TradingView
      </div>
    </div>
  )
}
