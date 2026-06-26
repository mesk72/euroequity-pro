import { NextResponse } from 'next/server'

export const revalidate = 900 // cache 15 minuti

const LEEWAY_KEY = process.env.LEEWAY_KEY || '8vawyvxmy5eq6y3pifohcw'
const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'

const INDICES = [
  // Americas
  { name: 'S&P 500',    symbol: 'GSPC.INDX',    region: 'americas' },
  { name: 'Nasdaq',     symbol: 'IXIC.INDX',     region: 'americas' },
  { name: 'Dow Jones',  symbol: 'DJI.INDX',      region: 'americas' },
  { name: 'TSX',        symbol: 'OSPTSX.INDX',   region: 'americas' },
  // Europe
  { name: 'DAX',        symbol: 'GDAXI.INDX',    region: 'europe' },
  { name: 'CAC 40',     symbol: 'FCHI.INDX',     region: 'europe' },
  { name: 'FTSE MIB',   symbol: 'FTSEMIB.MI',    region: 'europe' },
  { name: 'FTSE 100',   symbol: 'FTSE.INDX',     region: 'europe' },
  { name: 'Euro Stoxx', symbol: 'STOXX50E.INDX',  region: 'europe' },
  { name: 'SMI',        symbol: 'SSMI.INDX',     region: 'europe' },
  { name: 'IBEX 35',    symbol: 'IBEX.INDX',     region: 'europe' },
  // Asia
  { name: 'Nikkei 225', symbol: 'N225.INDX',     region: 'asia' },
  { name: 'Hang Seng',  symbol: 'HSI.INDX',      region: 'asia' },
  { name: 'ASX 200',    symbol: 'AXJO.INDX',     region: 'asia' },
]

async function fetchIndex(symbol: string, name: string) {
  try {
    const today = new Date().toISOString().slice(0, 10)
    const from  = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    const url = `${LEEWAY_BASE}/historicalquotes/${symbol}?apitoken=${LEEWAY_KEY}&from=${from}&to=${today}`
    const r = await fetch(url, {
      next: { revalidate: 900 },
      signal: AbortSignal.timeout(8000),
    })
    if (!r.ok) return null
    const data = await r.json()
    if (!Array.isArray(data) || data.length === 0) return null

    // Ordina per data ASC — usa close (non adjusted_close per gli indici)
    const sorted = data.sort((a: any, b: any) => a.date.localeCompare(b.date))
    const last   = sorted[sorted.length - 1]
    const prev   = sorted[sorted.length - 2]

    const price    = parseFloat(last.close)
    const prevPrice = prev ? parseFloat(prev.close) : null
    const changePct = prevPrice ? ((price - prevPrice) / prevPrice * 100) : null

    return {
      name,
      symbol,
      price: price.toLocaleString('en-US', { maximumFractionDigits: 2 }),
      changePct: changePct !== null ? (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%' : null,
      up: changePct !== null ? changePct >= 0 : null,
      date: last.date,
    }
  } catch { return null }
}

export async function GET() {
  const results = await Promise.all(
    INDICES.map(idx => fetchIndex(idx.symbol, idx.name).then(r => r ? { ...r, region: idx.region } : null))
  )

  const quotes = results.filter(Boolean)
  const americas = quotes.filter((q: any) => q.region === 'americas')
  const europe   = quotes.filter((q: any) => q.region === 'europe')
  const asia     = quotes.filter((q: any) => q.region === 'asia')

  const response = NextResponse.json({ americas, europe, asia, all: quotes })
  response.headers.set('Cache-Control', 'public, s-maxage=900, stale-while-revalidate=1800')
  return response
}
