import { NextResponse } from 'next/server'

const SYMBOLS = [
  { name: 'DAX',           symbol: '^GDAXI'     },
  { name: 'CAC 40',        symbol: '^FCHI'      },
  { name: 'FTSE MIB',      symbol: 'FTSEMIB.MI' },
  { name: 'FTSE 100',      symbol: '^FTSE'      },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E'  },
  { name: 'Nikkei 225',    symbol: '^N225'      },
  { name: 'Hang Seng',     symbol: '^HSI'       },
  { name: 'ASX 200',       symbol: '^AXJO'      },
]

export const revalidate = 60

export async function GET() {
  try {
    const syms = SYMBOLS.map(s => encodeURIComponent(s.symbol)).join(',')
    const url = 'https://query2.finance.yahoo.com/v8/finance/spark?symbols=' + syms + '&range=1d&interval=5m'
    
    const r = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.yahoo.com/',
        'Accept': '*/*',
        'Origin': 'https://finance.yahoo.com',
      },
      signal: AbortSignal.timeout(10000),
      cache: 'no-store',
    })

    if (!r.ok) {
      console.error('Yahoo spark error:', r.status, await r.text())
      return NextResponse.json({ quotes: [] })
    }

    const data = await r.json()
    const spark = data?.spark?.result || []

    const quotes = SYMBOLS.map(s => {
      const found = spark.find((item: any) => item.symbol === s.symbol)
      if (!found) return null
      const resp = found.response?.[0]
      if (!resp) return null
      const closes = resp.indicators?.quote?.[0]?.close || []
      const meta = resp.meta
      const price = meta?.regularMarketPrice || closes[closes.length - 1]
      const prevClose = meta?.chartPreviousClose || meta?.previousClose
      if (!price) return null
      const changePct = prevClose ? ((price - prevClose) / prevClose) * 100 : 0
      return {
        name: s.name,
        price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
        changePct: (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%',
        up: changePct >= 0,
      }
    }).filter(Boolean)

    return NextResponse.json({ quotes })
  } catch (e: any) {
    console.error('indices error:', e.message)
    return NextResponse.json({ quotes: [] })
  }
}
