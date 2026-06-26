'use client'

import { useEffect, useRef } from 'react'

const AMERICAS = [
  { name: 'S&P 500',   url: 'https://finance.yahoo.com/quote/%5EGSPC/' },
  { name: 'Nasdaq',    url: 'https://finance.yahoo.com/quote/%5EIXIC/' },
  { name: 'Dow Jones', url: 'https://finance.yahoo.com/quote/%5EDJI/'  },
  { name: 'TSX',       url: 'https://finance.yahoo.com/quote/%5EGSPTSE/'},
]

const EUROPE = [
  { name: 'DAX',        url: 'https://finance.yahoo.com/quote/%5EGDAXI/'    },
  { name: 'CAC 40',     url: 'https://finance.yahoo.com/quote/%5EFCHI/'     },
  { name: 'FTSE MIB',   url: 'https://finance.yahoo.com/quote/FTSEMIB.MI/'  },
  { name: 'FTSE 100',   url: 'https://finance.yahoo.com/quote/%5EFTSE/'     },
  { name: 'Euro Stoxx', url: 'https://finance.yahoo.com/quote/%5ESTOXX50E/' },
  { name: 'SMI',        url: 'https://finance.yahoo.com/quote/%5ESSMI/'     },
  { name: 'IBEX 35',    url: 'https://finance.yahoo.com/quote/%5EIBEX/'     },
]

const ASIA = [
  { name: 'Nikkei 225', url: 'https://finance.yahoo.com/quote/%5EN225/' },
  { name: 'Hang Seng',  url: 'https://finance.yahoo.com/quote/%5EHSI/'  },
  { name: 'ASX 200',    url: 'https://finance.yahoo.com/quote/%5EAXJO/' },
]

function IndexBar({ label, indices }: { label: string; indices: { name: string; url: string }[] }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '3px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.06)', overflowX: 'auto',
      flexWrap: 'nowrap', gap: 0 }}>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text4)',
        letterSpacing: '0.08em', textTransform: 'uppercase',
        minWidth: 64, flexShrink: 0 }}>
        {label}
      </span>
      {indices.map(idx => (
        <a key={idx.name} href={idx.url} target="_blank" rel="noopener noreferrer"
          style={{ fontSize: 10, fontWeight: 700, color: 'var(--text3)',
            textDecoration: 'none', marginRight: 10, flexShrink: 0,
            padding: '1px 7px', border: '1px solid var(--border)', borderRadius: 3 }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--orange)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--text3)')}>
          {idx.name} ↗
        </a>
      ))}
    </div>
  )
}

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!tvRef.current) return
    tvRef.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: [
        { proName: 'TVC:GOLD',  title: 'Gold'    },
        { proName: 'TVC:USOIL', title: 'Oil WTI' },
        { proName: 'FX:EURUSD', title: 'EUR/USD' },
        { proName: 'FX:USDJPY', title: 'USD/JPY' },
        { proName: 'FX:GBPUSD', title: 'GBP/USD' },
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
      <IndexBar label="Americas" indices={AMERICAS} />
      <IndexBar label="Europe"   indices={EUROPE}   />
      <IndexBar label="Asia Pac" indices={ASIA}     />
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
    </div>
  )
}
