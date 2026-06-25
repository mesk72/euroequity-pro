'use client'

import { useEffect, useRef } from 'react'

export default function MarketStrip() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    ref.current.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      colorTheme: 'dark',
      dateRange: '1D',
      showChart: false,
      locale: 'en',
      width: '100%',
      height: 70,
      isTransparent: true,
      showSymbolLogo: false,
      showFloatingTooltip: false,
      tabs: [
        {
          title: 'Indices',
          symbols: [
            { s: 'AMEX:SPY',       d: 'S&P 500'       },
            { s: 'NASDAQ:QQQ',     d: 'Nasdaq 100'     },
            { s: 'AMEX:DIA',       d: 'Dow Jones'      },
            { s: 'INDEX:DAX',      d: 'DAX'            },
            { s: 'INDEX:CAC40',    d: 'CAC 40'         },
            { s: 'INDEX:FTSEMIB',  d: 'FTSE MIB'       },
            { s: 'INDEX:UKX',      d: 'FTSE 100'       },
            { s: 'INDEX:SX5E',     d: 'Euro Stoxx 50'  },
            { s: 'INDEX:NKY',      d: 'Nikkei 225'     },
            { s: 'INDEX:HSI',      d: 'Hang Seng'      },
            { s: 'INDEX:AS51',     d: 'ASX 200'        },
          ],
        },
        {
          title: 'Commodities',
          symbols: [
            { s: 'TVC:GOLD',   d: 'Gold'      },
            { s: 'TVC:USOIL',  d: 'Oil WTI'   },
            { s: 'TVC:UKOIL',  d: 'Oil Brent' },
          ],
        },
        {
          title: 'FX',
          symbols: [
            { s: 'FX:EURUSD', d: 'EUR/USD' },
            { s: 'FX:USDJPY', d: 'USD/JPY' },
            { s: 'FX:GBPUSD', d: 'GBP/USD' },
            { s: 'FX:USDCHF', d: 'USD/CHF' },
          ],
        },
      ],
    })
    ref.current.appendChild(script)
  }, [])

  return (
    <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
      <div className="tradingview-widget-container" ref={ref}>
        <div className="tradingview-widget-container__widget" />
      </div>
      <div style={{ fontSize: 9, color: 'var(--text4)', padding: '2px 8px 4px', textAlign: 'right' }}>
        Powered by TradingView · live data
      </div>
    </div>
  )
}
