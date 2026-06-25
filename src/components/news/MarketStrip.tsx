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
        { proName: 'CME_MINI:ES1!',    title: 'S&P 500 (fut.)'   },
        { proName: 'CME_MINI:NQ1!',    title: 'Nasdaq 100 (fut.)' },
        { proName: 'CBOT_MINI:YM1!',   title: 'Dow Jones (fut.)'  },
        { proName: 'ICMARKETS:UK100',  title: 'FTSE 100 (fut.)'   },
        { proName: 'INDEX:DAX',        title: 'DAX'               },
        { proName: 'INDEX:CAC40',      title: 'CAC 40'            },
        { proName: 'INDEX:FTSEMIB',    title: 'FTSE MIB'          },
        { proName: 'INDEX:SX5E',       title: 'Euro Stoxx 50'     },
        { proName: 'INDEX:SXXP',       title: 'Stoxx 600'         },
        { proName: 'INDEX:NKY',        title: 'Nikkei 225'     },
        { proName: 'INDEX:HSI',        title: 'Hang Seng'      },
        { proName: 'ASX:XJO',          title: 'ASX 200'        },
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
        Prices powered by TradingView · S&P 500, Nasdaq, Dow, FTSE 100 = futures (live 24/7) · EU/Asia indices = real-time · delayed 15-20 min
      </div>
    </div>
  )
}
