import { NextResponse } from 'next/server'

const SYMBOLS = [
  { name: 'DAX',           symbol: '^GDAXI' },
  { name: 'CAC 40',        symbol: '^FCHI'  },
  { name: 'FTSE MIB',      symbol: 'FTSEMIB.MI' },
  { name: 'FTSE 100',      symbol: '^FTSE'  },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E' },
  { name: 'Nikkei 225',    symbol: '^N225'  },
  { name: 'Hang Seng',     symbol: '^HSI'   },
  { name: 'ASX 200',       symbol: '^AXJO'  },
]

export async function GET() {
  try {
    const syms = SYMBOLS.map(s => s.symbol).join(',')
    const url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols=' + encodeURIComponent(syms) + '&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent'
    const r = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://finance.yahoo.com',
      },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    if (!r.ok) return NextResponse.json({ quotes: [] })
    const data = await r.json()
    const results = data?.quoteResponse?.result || []
    const quotes = SYMBOLS.map(s => {
      const q = results.find((item: any) => item.symbol === s.symbol)
      if (!q) return null
      const price = q.regularMarketPrice
      const changePct = q.regularMarketChangePercent
      const change = q.regularMarketChange
      return {
        name: s.name, symbol: s.symbol,
        price: price != null ? price.toLocaleString('en-US', { maximumFractionDigits: 0 }) : '-',
        changePct: changePct != null ? (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%' : '-',
        up: changePct != null && changePct >= 0,
      }
    }).filter(Boolean)
    return NextResponse.json({ quotes })
  } catch {
    return NextResponse.json({ quotes: [] })
  }
}
