'use client'

import { useEffect, useRef } from 'react'

export default function MarketStrip() {
  const tvRef = useRef<HTMLDivElement>(null)
  const invRef = useRef<HTMLDivElement>(null)

  // TradingView - US ETF, commodities, FX
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

  // Investing.com - indici EU e Asia live
  useEffect(() => {
    if (!invRef.current) return
    invRef.current.innerHTML = ''
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.src = 'https://tvc4.investing.com/c0a65bc21ca5f30d82e0f7e6b17f4244/1719900000/1/1/8/ticker'
    script.async = true
    invRef.current.appendChild(script)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      {/* TradingView strip */}
      <div className="tradingview-widget-container" ref={tvRef}>
        <div className="tradingview-widget-container__widget" />
      </div>
      {/* Investing.com indices */}
      <div ref={invRef} style={{ minHeight: 30 }} />
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        Powered by TradingView & Investing.com · live data
      </div>
    </div>
  )
}
