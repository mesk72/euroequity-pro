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
        { proName: 'FOREXCOM:SPXUSD', title: 'S&P 500 Index' },
        { proName: 'FOREXCOM:NSXUSD', title: 'Nasdaq 100' },
        { proName: 'FOREXCOM:DJI',    title: 'Dow Jones' },
        { proName: 'FOREXCOM:UKXGBP', title: 'FTSE 100' },
        { proName: 'FOREXCOM:DEU40',  title: 'DAX' },
        { proName: 'FOREXCOM:FRA40',  title: 'CAC 40' },
        { proName: 'FOREXCOM:ITA40',  title: 'FTSE MIB' },
        { proName: 'FOREXCOM:EU50',   title: 'Euro Stoxx 50' },
        { proName: 'FOREXCOM:JPN225', title: 'Nikkei 225' },
        { proName: 'FOREXCOM:HKG33',  title: 'Hang Seng' },
        { proName: 'FOREXCOM:AUS200', title: 'ASX 200' },
        { proName: 'COMEX:GC1!',      title: 'Gold' },
        { proName: 'NYMEX:CL1!',      title: 'Oil WTI' },
        { proName: 'NYMEX:NG1!',      title: 'Nat Gas' },
        { proName: 'FX:EURUSD',       title: 'EUR/USD' },
        { proName: 'FX:USDJPY',       title: 'USD/JPY' },
        { proName: 'FX:GBPUSD',       title: 'GBP/USD' },
        { proName: 'FX:USDCHF',       title: 'USD/CHF' },
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
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        CFD prices · live when markets open · powered by TradingView
      </div>
    </div>
  )
}
