/**
 * Leeway API client
 * All functions use Next.js built-in fetch caching:
 * - revalidate: 60s for prices (15-20 min delay anyway)
 * - revalidate: 3600s for fundamentals (updated daily)
 * - revalidate: 1800s for symbol lists
 *
 * Shared cache: if user A and B request ASML in the same minute,
 * only ONE API call is made. Both get the cached response.
 */

const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'
const LEEWAY_KEY  = process.env.LEEWAY_KEY || ''

async function leewayFetch(endpoint: string, revalidate = 60) {
  const url = `${LEEWAY_BASE}/${endpoint}?apitoken=${LEEWAY_KEY}`
  try {
    const res = await fetch(url, {
      next: { revalidate },
      headers: { 'Authorization': `Bearer ${LEEWAY_KEY}` },
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export async function getSymbols(exchange: string, isinPrefix: string) {
  const data = await leewayFetch(`general/symbols/${exchange}`, 1800)
  if (!Array.isArray(data)) return []
  return data.filter((s: any) => {
    const isin = s.ISIN || s.isin || ''
    const type = (s.Type || s.type || '').toLowerCase()
    if (['etf','fund','preferred stock'].includes(type)) return false
    if (isinPrefix && !isin.startsWith(isinPrefix)) return false
    return true
  })
}

export async function getLiveQuotes(exchange: string) {
  const data = await leewayFetch(`livequotes/${exchange}`, 60)
  if (!Array.isArray(data)) return []
  return data
}

export async function getFundamentals(ticker: string, exchange: string) {
  const data = await leewayFetch(`fundamentals/${ticker}.${exchange}`, 3600)
  if (!data || typeof data !== 'object') return null
  return data
}

export async function getPriceHistory(ticker: string, exchange: string, days = 400) {
  const from = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10)
  const to   = new Date().toISOString().slice(0, 10)
  const data = await leewayFetch(
    `historicalquotes/${ticker}.${exchange}?from=${from}&to=${to}`, 3600
  )
  if (!Array.isArray(data)) return []
  return data
}

export async function searchByISIN(isin: string) {
  const data = await leewayFetch(`general/isin/${isin}`, 3600)
  return data
}

// Parse fundamentals into normalized Stock fields
export function parseFundamentals(raw: any) {
  const n = (v: any) => {
    const f = parseFloat(v)
    return isNaN(f) ? null : f
  }

  const epsCurrent = n(raw.epsEstimateCurrent || raw.epsEstimateCurrentYear)
  const eps30d     = n(raw.epsEstimate30daysAgo || raw.epsTrend30daysAgo)
  const epsMom30d  = epsCurrent != null && eps30d != null && eps30d !== 0
    ? ((epsCurrent - eps30d) / Math.abs(eps30d)) * 100
    : null

  let mktCap = n(raw.marketCapitalization || raw.marketCap)
  if (mktCap && mktCap > 1e6) mktCap = mktCap / 1e9 // to billions

  return {
    sector:    raw.sector || raw.Sector || null,
    peTrail:   n(raw.peRatio || raw.pe || raw.trailingPE),
    peFwd:     n(raw.forwardPE || raw.forwardPe),
    pb:        n(raw.priceToBook || raw.pb),
    evEbitda:  n(raw.evEbitda || raw.enterpriseValueEbitda),
    mktCap,
    roe:       n(raw.returnOnEquity || raw.roe),
    divYield:  n(raw.dividendYield || raw.divYield),
    beta:      n(raw.beta),
    epsGrowth: n(raw.earningsGrowth || raw.epsGrowth),
    revGrowth: n(raw.revenueGrowth),
    epsMom30d,
  }
}

export function parseMomentum(history: any[]) {
  if (!history || history.length < 5) return {}
  const closes = history
    .map((d: any) => parseFloat(d.adjusted_close || d.close))
    .filter(v => !isNaN(v))
  const n    = closes.length
  const last = closes[n - 1]
  const mom  = (offset: number) =>
    n >= offset ? (last / closes[Math.max(0, n - offset)] - 1) * 100 : null
  return {
    mom1w:  mom(5),
    mom1m:  mom(21),
    mom6m:  mom(126),
    mom12m: mom(252),
  }
}
