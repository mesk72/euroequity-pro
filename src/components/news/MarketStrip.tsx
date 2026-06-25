'use client'

import { useEffect, useRef } from 'react'

const EU_LINKS = [
  { name: 'DAX',           url: 'https://finance.yahoo.com/quote/%5EGDAXI/' },
  { name: 'CAC 40',        url: 'https://finance.yahoo.com/quote/%5EFCHI/'  },
  { name: 'FTSE 100',      url: 'https://finance.yahoo.com/quote/%5EFTSE/'  },
  { name: 'FTSE MIB',      url: 'https://finance.yahoo.com/quote/FTSEMIB.MI/' },
  { name: 'Euro Stoxx 50', url: 'https://finance.yahoo.com/quote/%5ESTOXX50E/' },
]

const ASIA_LINKS = [
  { name: 'Nikkei 225', url: 'https://finance.yahoo.com/quote/%5EN225/' },
  { name: 'Hang Seng',  url: 'https://finance.yahoo.com/quote/%5EHSI/'  },
  { name: 'ASX 200',    url: 'https://finance.yahoo.com/quote/%5EAXJO/' },
]

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

  const linkStyle = {
    fontSize: 10, fontWeight: 700, color: 'var(--text3)',
    textDecoration: 'none', padding: '2px 8px',
    border: '1px solid var(--border)', borderRadius: 3,
    whiteSpace: 'nowrap' as const,
  }

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
      <div style={{ display: 'flex', gap: 8, padding: '5px 12px', overflowX: 'auto', alignItems: 'center', flexWrap: 'nowrap' }}>
        <span style={{ fontSize: 9, color: 'var(--text4)', flexShrink: 0 }}>🌍 EU:</span>
        {EU_LINKS.map(l => (
          <a key={l.name} href={l.url} target="_blank" rel="noopener noreferrer" style={linkStyle}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--orange)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text3)')}>
            {l.name} ↗
          </a>
        ))}
        <span style={{ fontSize: 9, color: 'var(--text4)', flexShrink: 0, marginLeft: 8 }}>🌏 Asia:</span>
        {ASIA_LINKS.map(l => (
          <a key={l.name} href={l.url} target="_blank" rel="noopener noreferrer" style={linkStyle}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--orange)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text3)')}>
            {l.name} ↗
          </a>
        ))}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        TradingView (US/Commodities/FX live) · Yahoo Finance links (EU/Asia)
      </div>
    </div>
  )
}
