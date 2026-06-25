'use client'

import { useEffect, useRef } from 'react'

export default function MarketStrip() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    ref.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      symbols: [
        { proName: 'FOREXCOM:SPXUSD', title: 'S&P 500' },
        { proName: 'FOREXCOM:NSXUSD', title: 'Nasdaq 100' },
        { proName: 'FOREXCOM:DJI',    title: 'Dow Jones' },
        { proName: 'SPREADEX:DAX',    title: 'DAX' },
        { proName: 'SPREADEX:FTSE',   title: 'FTSE 100' },
        { proName: 'SPREADEX:CAC',    title: 'CAC 40' },
        { proName: 'SPREADEX:MIB',    title: 'FTSE MIB' },
        { proName: 'SPREADEX:NKY',    title: 'Nikkei 225' },
        { proName: 'SPREADEX:HSI',    title: 'Hang Seng' },
        { proName: 'SPREADEX:AS51',   title: 'ASX 200' },
        { proName: 'COMEX:GC1!',      title: 'Gold' },
        { proName: 'NYMEX:CL1!',      title: 'Oil WTI' },
        { proName: 'NYMEX:NG1!',      title: 'Nat Gas' },
        { proName: 'FX:EURUSD',       title: 'EUR/USD' },
        { proName: 'FX:USDJPY',       title: 'USD/JPY' },
        { proName: 'FX:GBPUSD',       title: 'GBP/USD' },
        { proName: 'FX:USDCHF',       title: 'USD/CHF' },
        { proName: 'CRYPTOCAP:BTC',   title: 'Bitcoin' },
      ],
      showSymbolLogo: false,
      isTransparent: true,
      displayMode: 'adaptive',
      colorTheme: 'dark',
      locale: 'en',
    })
    ref.current.appendChild(script)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <div className="tradingview-widget-container" ref={ref}>
        <div className="tradingview-widget-container__widget" />
      </div>
    </div>
  )
}
