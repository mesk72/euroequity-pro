import { NextRequest, NextResponse } from 'next/server'

export const revalidate = 120 // 2 min cache shared

const LEEWAY_KEY  = process.env.LEEWAY_KEY || ''
const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'

const INDICES = [
  { name: 'Euro Stoxx 50',      ticker: 'STOXX50E', exchange: 'INDX' },
  { name: 'FTSE MIB',           ticker: 'FTSEMIB',  exchange: 'INDX' },
  { name: 'FTSE MIB All Share', ticker: 'ITLMS',    exchange: 'INDX' },
  { name: 'DAX',                ticker: 'GDAXI',    exchange: 'INDX' },
  { name: 'CAC 40',             ticker: 'FCHI',     exchange: 'INDX' },
  { name: 'AEX',                ticker: 'AEX',      exchange: 'INDX' },
  { name: 'IBEX 35',            ticker: 'IBEX',     exchange: 'INDX' },
  { name: 'BEL 20',             ticker: 'BFX',      exchange: 'INDX' },
  { name: 'PSI',                ticker: 'PSI20',    exchange: 'INDX' },
  { name: 'ATX',                ticker: 'ATX',      exchange: 'VI'   },
  { name: 'OMX Helsinki 25',    ticker: 'OMXH25',   exchange: 'HE'   },
  { name: 'ISEQ',               ticker: 'ISEQ',     exchange: 'IR'   },
  { name: 'ASE',                ticker: 'ATG',      exchange: 'AT'   },
]

async function fetchQuote(ticker: string, exchange: string) {
  // Try Leeway live quote
  try {
    const url = `${LEEWAY_BASE}/livequotes/${ticker}.${exchange}?apitoken=${LEEWAY_KEY}`
    const r   = await fetch(url, { next: { revalidate: 120 } })
    if (r.ok) {
      const data = await r.json()
      const d    = Array.isArray(data) ? data[0] : data
      if (d?.close || d?.price) {
        const close = parseFloat(d.close || d.price)
        const prev  = parseFloat(d.previousClose || d.prev_close || 0)
        const changeP = prev && prev !== 0 ? (close / prev - 1) * 100 : null
        return {
          close,
          changeP,
          timestamp: d.timestamp || null,
        }
      }
    }
  } catch {}

  // Try Leeway historical (last 2 days) as fallback
  try {
    const from = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10)
    const to   = new Date().toISOString().slice(0, 10)
    const url  = `${LEEWAY_BASE}/historicalquotes/${ticker}.${exchange}?from=${from}&to=${to}&apitoken=${LEEWAY_KEY}`
    const r    = await fetch(url, { next: { revalidate: 120 } })
    if (r.ok) {
      const hist = await r.json()
      if (Array.isArray(hist) && hist.length >= 2) {
        const last   = hist[hist.length - 1]
        const prev   = hist[hist.length - 2]
        const close  = parseFloat(last.close || last.adjusted_close)
        const prevPx = parseFloat(prev.close || prev.adjusted_close)
        const changeP = prevPx ? (close / prevPx - 1) * 100 : null
        return { close, changeP, timestamp: null }
      }
      if (Array.isArray(hist) && hist.length === 1) {
        const last = hist[0]
        const close = parseFloat(last.close || last.adjusted_close)
        const open  = parseFloat(last.open)
        const changeP = open ? (close / open - 1) * 100 : null
        return { close, changeP, timestamp: null }
      }
    }
  } catch {}

  return null
}

export async function GET(req: NextRequest) {
  const results = await Promise.all(
    INDICES.map(async (idx) => {
      const quote = await fetchQuote(idx.ticker, idx.exchange)
      return {
        name:      idx.name,
        ticker:    `${idx.ticker}.${idx.exchange}`,
        close:     quote?.close    ?? null,
        changeP:   quote?.changeP  ?? null,
        timestamp: quote?.timestamp ?? null,
      }
    })
  )

  return NextResponse.json({ indices: results })
}
