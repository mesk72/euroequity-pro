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
        { proName: 'CAPITALCOM:US500',  title: 'S&P 500'        },
        { proName: 'CAPITALCOM:US100',  title: 'Nasdaq 100'     },
        { proName: 'CAPITALCOM:US30',   title: 'Dow Jones'      },
        { proName: 'CAPITALCOM:UK100',  title: 'FTSE 100'       },
        { proName: 'CAPITALCOM:DE40',   title: 'DAX'            },
        { proName: 'CAPITALCOM:FR40',   title: 'CAC 40'         },
        { proName: 'CAPITALCOM:IT40',   title: 'FTSE MIB'       },
        { proName: 'CAPITALCOM:EU50',   title: 'Euro Stoxx 50'  },
        { proName: 'CAPITALCOM:JP225',  title: 'Nikkei 225'     },
        { proName: 'CAPITALCOM:HK50',   title: 'Hang Seng'      },
        { proName: 'CAPITALCOM:AUS200', title: 'ASX 200'        },
        { proName: 'TVC:GOLD',         title: 'Gold'           },
        { proName: 'TVC:USOIL',        title: 'Oil WTI'        },
        { proName: 'TVC:UKOIL',        title: 'Oil Brent'      },
        { proName: 'FX:EURUSD',        title: 'EUR/USD'        },
        { proName: 'FX:USDJPY',        title: 'USD/JPY'        },
        { proName: 'FX:GBPUSD',        title: 'GBP/USD'        },
        { proName: 'FX:USDCHF',        title: 'USD/CHF'        },
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
        Prices powered by TradingView · All indices = CFD live 24/7 · Data may differ slightly from cash index
      </div>
    </div>
  )
}
