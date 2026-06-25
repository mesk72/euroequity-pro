import { NextResponse } from 'next/server'

const FMP_KEY = 'aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk'

const ASIA_INDICES = [
  { name: 'Nikkei 225', symbol: '^N225'  },
  { name: 'Hang Seng',  symbol: '^HSI'   },
  { name: 'ASX 200',    symbol: '^AXJO'  },
]

const EU_INDICES = [
  { name: 'DAX',           symbol: '^GDAXI'    },
  { name: 'CAC 40',        symbol: '^FCHI'     },
  { name: 'FTSE MIB',      symbol: 'FTSEMIB.MI'},
  { name: 'FTSE 100',      symbol: '^FTSE'     },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E' },
]

function isAsiaOpen(): boolean {
  const now = new Date()
  const utcH = now.getUTCHours()
  const utcM = now.getUTCMinutes()
  const utcTime = utcH * 60 + utcM
  // Asia: 00:00 - 08:00 UTC (Tokyo 09:00-17:00 JST, HK 09:30-16:00 HKT)
  return utcTime >= 0 && utcTime <= 480
}

function isEUOpen(): boolean {
  const now = new Date()
  const utcH = now.getUTCHours()
  const utcM = now.getUTCMinutes()
  const utcTime = utcH * 60 + utcM
  // EU: 07:00 - 15:30 UTC (09:00-17:30 CET)
  return utcTime >= 420 && utcTime <= 930
}

async function fetchFMP(symbols: string[]): Promise<any[]> {
  try {
    const syms = symbols.join(',')
    const url = `https://financialmodelingprep.com/api/v3/quote/${encodeURIComponent(syms)}?apikey=${FMP_KEY}`
    const r = await fetch(url, {
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    if (!r.ok) return []
    return await r.json()
  } catch { return [] }
}

export async function GET() {
  const asiaOpen = isAsiaOpen()
  const euOpen = isEUOpen()

  const toFetch: { name: string; symbol: string }[] = []
  if (asiaOpen) toFetch.push(...ASIA_INDICES)
  if (euOpen) toFetch.push(...EU_INDICES)

  if (toFetch.length === 0) {
    // Fuori orario - restituisce ultimo prezzo senza chiamate API
    return NextResponse.json({ quotes: [], marketsClosed: true })
  }

  const symbols = toFetch.map(i => i.symbol)
  const data = await fetchFMP(symbols)

  const quotes = toFetch.map(idx => {
    const q = data.find((d: any) => d.symbol === idx.symbol)
    if (!q) return null
    const pct = q.changesPercentage || 0
    return {
      name: idx.name,
      price: (q.price || 0).toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
      up: pct >= 0,
    }
  }).filter(Boolean)

  return NextResponse.json({ quotes })
}
