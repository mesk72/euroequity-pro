import { NextResponse } from 'next/server'

const FMP_KEY = 'aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk'

const ASIA_INDICES = [
  { name: 'Nikkei 225', symbol: '^N225'  },
  { name: 'Hang Seng',  symbol: '^HSI'   },
  { name: 'ASX 200',    symbol: '^AXJO'  },
]

const EU_INDICES = [
  { name: 'DAX',           symbol: '^GDAXI'   },
  { name: 'CAC 40',        symbol: '^FCHI'    },
  { name: 'FTSE MIB',      symbol: '^FTSEMIB' },
  { name: 'FTSE 100',      symbol: '^FTSE'    },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E'},
]

function isWeekday(): boolean {
  const day = new Date().getUTCDay()
  return day >= 1 && day <= 5 // Mon-Fri
}

function isAsiaOpen(): boolean {
  if (!isWeekday()) return false
  const now = new Date()
  const utcH = now.getUTCHours()
  const utcM = now.getUTCMinutes()
  const utcTime = utcH * 60 + utcM
  // Tokyo 00:00-06:00 UTC, HK 01:30-08:00 UTC, ASX 00:00-06:00 UTC
  return utcTime >= 0 && utcTime <= 480
}

function isEUOpen(): boolean {
  if (!isWeekday()) return false
  const now = new Date()
  const utcH = now.getUTCHours()
  const utcM = now.getUTCMinutes()
  const utcTime = utcH * 60 + utcM
  // EU: 07:00 - 15:30 UTC (09:00-17:30 CET / 08:00-16:30 UTC in estate)
  return utcTime >= 420 && utcTime <= 930
}

async function fetchFMP(symbols: string[]): Promise<{ data: any[], url: string, status: number, raw: string }> {
  const syms = symbols.map(s => encodeURIComponent(s)).join(',')
  const url = `https://financialmodelingprep.com/api/v4/batch-pre-post-market?symbols=${syms}&apikey=${FMP_KEY}`
  try {
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    const raw = await r.text()
    let data = []
    try { data = JSON.parse(raw); if (!Array.isArray(data)) data = [] } catch {}
    return { data, url, status: r.status, raw: raw.slice(0, 300) }
  } catch (e: any) {
    return { data: [], url, status: 0, raw: e.message }
  }
}

export async function GET() {
  const asiaOpen = isAsiaOpen()
  const euOpen = isEUOpen()

  const toFetch: { name: string; symbol: string }[] = []
  if (asiaOpen) toFetch.push(...ASIA_INDICES)
  if (euOpen) toFetch.push(...EU_INDICES)

  if (toFetch.length === 0) {
    return NextResponse.json({ quotes: [], debug: 'markets closed', utcHour: new Date().getUTCHours() })
  }

  const symbols = toFetch.map(i => i.symbol)
  const fmpResult = await fetchFMP(symbols)
  const fmpData = fmpResult.data

  const quotes = toFetch.map(idx => {
    const q = fmpData.find((d: any) => d.symbol === idx.symbol)
    if (!q) return null
    const pct = q.changesPercentage || 0
    return {
      name: idx.name,
      price: (q.price || 0).toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
      up: pct >= 0,
    }
  }).filter(Boolean)

  return NextResponse.json({
    quotes,
    debug: {
      asiaOpen,
      euOpen,
      utcHour: new Date().getUTCHours(),
      symbolsFetched: symbols,
      fmpCount: fmpData.length,
      fmpStatus: fmpResult.status,
      fmpUrl: fmpResult.url,
      fmpRaw: fmpResult.raw,
    }
  })
}
