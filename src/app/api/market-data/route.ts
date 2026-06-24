import { NextResponse } from 'next/server'

const SYMBOLS = {
  indices: [
    { symbol: '^GSPC',  name: 'S&P 500',    region: 'americas' },
    { symbol: '^IXIC',  name: 'Nasdaq',      region: 'americas' },
    { symbol: '^DJI',   name: 'Dow Jones',   region: 'americas' },
    { symbol: '^GDAXI', name: 'DAX',         region: 'europe'   },
    { symbol: '^FTSE',  name: 'FTSE 100',    region: 'europe'   },
    { symbol: '^FCHI',  name: 'CAC 40',      region: 'europe'   },
    { symbol: '^STOXX50E', name: 'Euro Stoxx 50', region: 'europe' },
    { symbol: 'FTSEMIB.MI', name: 'FTSE MIB', region: 'europe' },
    { symbol: '^N225',  name: 'Nikkei 225',  region: 'asia'     },
    { symbol: '^HSI',   name: 'Hang Seng',   region: 'asia'     },
    { symbol: '^AXJO',  name: 'ASX 200',     region: 'asia'     },
    { symbol: '^KS11',  name: 'KOSPI',       region: 'asia'     },
  ],
  commodities: [
    { symbol: 'GC=F',  name: 'Gold'    },
    { symbol: 'CL=F',  name: 'Oil WTI' },
    { symbol: 'BZ=F',  name: 'Oil Brent' },
  ],
  fx: [
    { symbol: 'EURUSD=X', name: 'EUR/USD' },
    { symbol: 'USDJPY=X', name: 'USD/JPY' },
    { symbol: 'GBPUSD=X', name: 'GBP/USD' },
    { symbol: 'USDCHF=X', name: 'USD/CHF' },
  ],
}

async function fetchYahooQuotes(symbols: string[]): Promise<Record<string, any>> {
  try {
    const syms = symbols.join(',')
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(syms)}&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketPreviousClose,shortName`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' },
      signal: AbortSignal.timeout(10000),
      cache: 'no-store',
    })
    if (!r.ok) return {}
    const d = await r.json()
    const result: Record<string, any> = {}
    for (const q of (d?.quoteResponse?.result || [])) {
      result[q.symbol] = {
        price: q.regularMarketPrice,
        change: q.regularMarketChange,
        changePct: q.regularMarketChangePercent,
        prevClose: q.regularMarketPreviousClose,
        name: q.shortName,
      }
    }
    return result
  } catch { return {} }
}

export async function GET() {
  const allSymbols = [
    ...SYMBOLS.indices.map(s => s.symbol),
    ...SYMBOLS.commodities.map(s => s.symbol),
    ...SYMBOLS.fx.map(s => s.symbol),
  ]

  const quotes = await fetchYahooQuotes(allSymbols)

  const indices = SYMBOLS.indices.map(s => ({
    ...s,
    ...quotes[s.symbol],
  }))

  const commodities = SYMBOLS.commodities.map(s => ({
    ...s,
    ...quotes[s.symbol],
  }))

  const fx = SYMBOLS.fx.map(s => ({
    ...s,
    ...quotes[s.symbol],
  }))

  return NextResponse.json({ indices, commodities, fx, timestamp: new Date().toISOString() })
}
