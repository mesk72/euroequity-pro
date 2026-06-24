'use client'

import { useEffect, useRef } from 'react'

const SYMBOLS = [
  // Americas
  { proName: 'FOREXCOM:SPXUSD', title: 'S&P 500' },
  { proName: 'NASDAQ:NDX', title: 'Nasdaq 100' },
  { proName: 'FOREXCOM:DJIA', title: 'Dow Jones' },
  // Europe
  { proName: 'XETR:DAX', title: 'DAX' },
  { proName: 'INDEX:UKX', title: 'FTSE 100' },
  { proName: 'EURONEXT:PX1', title: 'CAC 40' },
  { proName: 'MIL:FTSEMIB', title: 'FTSE MIB' },
  // Asia
  { proName: 'INDEX:NKY', title: 'Nikkei 225' },
  { proName: 'INDEX:HSI', title: 'Hang Seng' },
  { proName: 'ASX:XJO', title: 'ASX 200' },
  // Commodities
  { proName: 'COMEX:GC1!', title: 'Gold' },
  { proName: 'NYMEX:CL1!', title: 'Oil WTI' },
  { proName: 'NYMEX:NG1!', title: 'Nat Gas' },
  // FX
  { proName: 'FX:EURUSD', title: 'EUR/USD' },
  { proName: 'FX:USDJPY', title: 'USD/JPY' },
  { proName: 'FX:GBPUSD', title: 'GBP/USD' },
  { proName: 'FX:USDCHF', title: 'USD/CHF' },
]

export default function MarketStrip() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    ref.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: SYMBOLS,
      showSymbolLogo: false,
      isTransparent: true,
      displayMode: 'adaptive',
      colorTheme: 'dark',
      locale: 'en',
    })
    ref.current.appendChild(script)
  }, [])

  return (
    <div style={{ 
      borderBottom: '1px solid var(--border)', 
      marginBottom: 8,
      height: 46,
      overflow: 'hidden',
    }}>
      <div className="tradingview-widget-container" ref={ref} style={{ height: 46 }}>
        <div className="tradingview-widget-container__widget"></div>
      </div>
    </div>
  )
}
