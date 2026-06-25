import { NextResponse } from 'next/server'

const ASIA_INDICES = [
  { name: 'Nikkei 225', symbol: '^N225'  },
  { name: 'Hang Seng',  symbol: '^HSI'   },
  { name: 'ASX 200',    symbol: '^AXJO'  },
]

const EU_INDICES = [
  { name: 'DAX',           symbol: '^GDAXI'    },
  { name: 'CAC 40',        symbol: '^FCHI'     },
  { name: 'FTSE MIB',      symbol: '^FTMIB'    },
  { name: 'FTSE 100',      symbol: '^FTSE'     },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E' },
]

const YAHOO_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json',
  'Accept-Language': 'en-US,en;q=0.9',
  'Referer': 'https://finance.yahoo.com/',
  'Origin': 'https://finance.yahoo.com',
}

function isWeekday(): boolean {
  return new Date().getUTCDay() >= 1 && new Date().getUTCDay() <= 5
}

function isAsiaOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 0 && t <= 480
}

function isEUOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 420 && t <= 930
}

async function fetchBatch(symbols: string[]): Promise<{ data: any[], status: number, raw: string }> {
  try {
    const syms = symbols.map(s => encodeURIComponent(s)).join(',')
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${syms}&fields=regularMarketPrice,regularMarketChangePercent`
    const r = await fetch(url, { headers: YAHOO_HEADERS, signal: AbortSignal.timeout(8000), cache: 'no-store' })
    const raw = await r.text()
    let data: any[] = []
    try { const j = JSON.parse(raw); data = j?.quoteResponse?.result || [] } catch {}
    return { data, status: r.status, raw: raw.slice(0, 400) }
  } catch (e: any) { return { data: [], status: 0, raw: e.message } }
}

async function fetchSingle(symbol: string): Promise<any | null> {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`
    const r = await fetch(url, { headers: YAHOO_HEADERS, signal: AbortSignal.timeout(8000), cache: 'no-store' })
    if (!r.ok) return null
    const d = await r.json()
    const meta = d?.chart?.result?.[0]?.meta
    if (!meta) return null
    return {
      symbol,
      regularMarketPrice: meta.regularMarketPrice,
      regularMarketChangePercent: meta.regularMarketPrice && meta.chartPreviousClose
        ? ((meta.regularMarketPrice - meta.chartPreviousClose) / meta.chartPreviousClose) * 100
        : 0,
    }
  } catch { return null }
}

export async function GET() {
  const asiaOpen = isAsiaOpen()
  const euOpen = isEUOpen()
  const toFetch = [
    ...(asiaOpen ? ASIA_INDICES : []),
    ...(euOpen ? EU_INDICES : []),
  ]

  if (toFetch.length === 0) {
    return NextResponse.json({ quotes: [], debug: 'markets closed', utcHour: new Date().getUTCHours() })
  }

  const symbols = toFetch.map(i => i.symbol)

  // Prova batch prima
  const batchResult = await fetchBatch(symbols)
  let results = batchResult.data

  // Fallback: singole chiamate se batch fallisce
  if (results.length === 0) {
    results = (await Promise.all(symbols.map(fetchSingle))).filter(Boolean) as any[]
  }

  const quotes = toFetch.map(idx => {
    const q = results.find((d: any) => d.symbol === idx.symbol)
    if (!q) return null
    const price = q.regularMarketPrice || 0
    const pct = q.regularMarketChangePercent || 0
    return {
      name: idx.name,
      price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
      up: pct >= 0,
    }
  }).filter(Boolean)

  return NextResponse.json({
    quotes,
    debug: { asiaOpen, euOpen, utcHour: new Date().getUTCHours(), count: results.length, batchStatus: batchResult.status, batchRaw: batchResult.raw }
  })
}
