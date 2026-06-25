'use client'

import { useEffect, useRef, useState } from 'react'

interface Quote {
  name: string
  price: string
  changePct: string
  up: boolean
}

// Indici EU e Asia via Yahoo Finance proxy
const EU_INDICES = [
  { name: 'DAX',           sym: '%5EGDAXI'    },
  { name: 'CAC 40',        sym: '%5EFCHI'     },
  { name: 'FTSE MIB',      sym: 'FTSEMIB.MI'  },
  { name: 'FTSE 100',      sym: '%5EFTSE'     },
  { name: 'Euro Stoxx 50', sym: '%5ESTOXX50E' },
]

const ASIA_INDICES = [
  { name: 'Nikkei 225', sym: '%5EN225' },
  { name: 'Hang Seng',  sym: '%5EHSI'  },
  { name: 'ASX 200',    sym: '%5EAXJO' },
]

function isWeekday(): boolean {
  const d = new Date().getUTCDay()
  return d >= 1 && d <= 5
}

function isEUOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 420 && t <= 930
}

function isAsiaOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 0 && t <= 480
}

// Sezione indici inline
function IndexRow({ label, quotes, loading }: { label: string; quotes: Quote[] | null; loading: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, padding: '3px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.06)', flexWrap: 'nowrap', overflowX: 'auto' }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text4)', marginRight: 10,
        flexShrink: 0, letterSpacing: '0.08em', textTransform: 'uppercase', minWidth: 60 }}>
        {label}
      </span>
      {loading ? (
        <span style={{ fontSize: 9, color: 'var(--text4)' }}>Loading...</span>
      ) : quotes && quotes.length > 0 ? (
        quotes.map((q, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 16, flexShrink: 0 }}>
            <span style={{ fontSize: 10, color: 'var(--text4)', fontWeight: 600 }}>{q.name}</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', fontFamily: 'IBM Plex Mono' }}>{q.price}</span>
            <span style={{ fontSize: 10, fontWeight: 600, fontFamily: 'IBM Plex Mono',
              color: q.up ? '#22c55e' : '#ef4444' }}>{q.changePct}</span>
          </div>
        ))
      ) : (
        <span style={{ fontSize: 9, color: 'var(--text4)' }}>Market closed</span>
      )}
    </div>
  )
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const [euQuotes, setEuQuotes] = useState<Quote[] | null>(null)
  const [asiaQuotes, setAsiaQuotes] = useState<Quote[] | null>(null)
  const [loadingEU, setLoadingEU] = useState(false)
  const [loadingAsia, setLoadingAsia] = useState(false)

  // TradingView ticker tape - solo commodities e FX
  useEffect(() => {
    if (!tvRef.current) return
    tvRef.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: [
        { proName: 'TVC:GOLD',   title: 'Gold'     },
        { proName: 'TVC:USOIL',  title: 'Oil WTI'  },
        { proName: 'TVC:UKOIL',  title: 'Oil Brent'},
        { proName: 'FX:EURUSD',  title: 'EUR/USD'  },
        { proName: 'FX:USDJPY',  title: 'USD/JPY'  },
        { proName: 'FX:GBPUSD',  title: 'GBP/USD'  },
        { proName: 'FX:USDCHF',  title: 'USD/CHF'  },
        { proName: 'FX:USDCAD',  title: 'USD/CAD'  },
        { proName: 'FX:AUDUSD',  title: 'AUD/USD'  },
      ],
      showSymbolLogo: false,
      isTransparent: true,
      displayMode: 'adaptive',
      colorTheme: 'dark',
      locale: 'en',
    })
    tvRef.current.appendChild(script)
  }, [])

  // Indici EU e Asia via /api/indices
  useEffect(() => {
    const load = async () => {
      setLoadingEU(true); setLoadingAsia(true)
      try {
        const r = await fetch('/api/indices', { cache: 'no-store' })
        if (r.ok) {
          const d = await r.json()
          setEuQuotes(d.euQuotes || [])
          setAsiaQuotes(d.asiaQuotes || [])
        }
      } catch {}
      setLoadingEU(false); setLoadingAsia(false)
    }
    load()
    const t = setInterval(load, 900000)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>

      {/* Riga 1: Indici Nord America — Yahoo Finance links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, padding: '3px 8px',
        borderBottom: '1px solid rgba(255,255,255,0.06)', flexWrap: 'nowrap', overflowX: 'auto' }}>
        <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text4)', marginRight: 10,
          flexShrink: 0, letterSpacing: '0.08em', textTransform: 'uppercase', minWidth: 60 }}>
          Americas
        </span>
        {[
          { name: 'S&P 500',    url: 'https://finance.yahoo.com/quote/%5EGSPC/' },
          { name: 'Nasdaq 100', url: 'https://finance.yahoo.com/quote/%5EIXIC/' },
          { name: 'Dow Jones',  url: 'https://finance.yahoo.com/quote/%5EDJI/'  },
          { name: 'TSX',        url: 'https://finance.yahoo.com/quote/%5EGSPTSE/'},
        ].map(idx => (
          <a key={idx.name} href={idx.url} target="_blank" rel="noopener noreferrer"
            style={{ fontSize: 10, fontWeight: 700, color: 'var(--text3)', textDecoration: 'none',
              marginRight: 16, flexShrink: 0, padding: '1px 6px',
              border: '1px solid var(--border)', borderRadius: 3 }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--orange)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text3)')}>
            {idx.name} ↗
          </a>
        ))}
      </div>

      {/* Riga 2: Indici Europa */}
      <IndexRow label="Europe" quotes={euQuotes} loading={loadingEU} />

      {/* Riga 3: Indici Asia Pacific */}
      <IndexRow label="Asia Pac" quotes={asiaQuotes} loading={loadingAsia} />

      {/* Riga 4: TradingView - Commodities e FX */}
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>

      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 3px', textAlign: 'right' }}>
        Americas = Yahoo Finance links · EU/Asia = Yahoo Finance · Commodities/FX = TradingView live
      </div>
    </div>
  )
}
