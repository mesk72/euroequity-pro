// FMP (Financial Modeling Prep) API client
// Documentazione: https://financialmodelingprep.com/developer/docs

const FMP_BASE = 'https://financialmodelingprep.com/api/v3'
const FMP_KEY  = process.env.FMP_KEY || ''

async function fmpGet(endpoint: string, params: Record<string, string> = {}) {
  const url = new URL(`${FMP_BASE}/${endpoint}`)
  url.searchParams.set('apikey', FMP_KEY)
  for (const [k, v] of Object.entries(params)) {
    url.searchParams.set(k, v)
  }
  const r = await fetch(url.toString(), { cache: 'no-store' })
  if (!r.ok) return null
  return r.json()
}

// Quote live per un singolo ticker (es. "ENI.MI")
export async function getLiveQuote(ticker: string) {
  const data = await fmpGet(`quote/${ticker}`)
  if (!data || !data[0]) return null
  const q = data[0]
  return {
    ticker:    q.symbol,
    price:     q.price,
    change1d:  q.changesPercentage,
    changeAbs: q.change,
    volume:    q.volume,
    mktCap:    q.marketCap ? q.marketCap / 1e9 : null,
  }
}

// Quote bulk per un array di ticker
export async function getBulkQuotes(tickers: string[]) {
  if (!tickers.length) return []
  const symbols = tickers.join(',')
  const data = await fmpGet(`quote/${symbols}`)
  if (!Array.isArray(data)) return []
  return data.map((q: any) => ({
    ticker:    q.symbol,
    price:     q.price,
    change1d:  q.changesPercentage,
    changeAbs: q.change,
    volume:    q.volume,
    mktCap:    q.marketCap ? q.marketCap / 1e9 : null,
  }))
}

// Profilo + fondamentali
export async function getProfile(ticker: string) {
  const data = await fmpGet(`profile/${ticker}`)
  if (!Array.isArray(data) || !data[0]) return null
  const p = data[0]
  return {
    company:  p.companyName,
    sector:   p.sector,
    industry: p.industry,
    country:  p.country,
    isin:     p.isin,
    website:  p.website,
    mktCap:   p.mktCap ? p.mktCap / 1e9 : null,
    beta:     p.beta,
  }
}

// Key metrics (PE, PB, ROE, ecc.)
export async function getKeyMetrics(ticker: string) {
  const data = await fmpGet(`key-metrics-ttm/${ticker}`)
  if (!Array.isArray(data) || !data[0]) return null
  const m = data[0]
  return {
    peTrail:    m.peRatioTTM,
    pb:         m.pbRatioTTM,
    evEbitda:   m.enterpriseValueOverEBITDATTM,
    roe:        m.roeTTM ? m.roeTTM * 100 : null,
    roa:        m.roaTTM ? m.roaTTM * 100 : null,
    divYield:   m.dividendYieldTTM ? m.dividendYieldTTM * 100 : null,
    divPayout:  m.payoutRatioTTM ? m.payoutRatioTTM * 100 : null,
    netMargin:  m.netProfitMarginTTM ? m.netProfitMarginTTM * 100 : null,
  }
}

// Stime analisti (PE forward, EPS estimates)
export async function getAnalystEstimates(ticker: string) {
  const data = await fmpGet(`analyst-estimates/${ticker}`, { limit: '2' })
  if (!Array.isArray(data) || !data[0]) return null
  const e = data[0]
  const e1 = data[1]
  const epsEst  = e.estimatedEpsAvg
  const epsLast = e1?.estimatedEpsAvg || null
  const epsMom  = epsEst && epsLast && epsLast !== 0
    ? ((epsEst - epsLast) / Math.abs(epsLast)) * 100
    : null
  return {
    peFwd:     e.estimatedEpsAvg && e.estimatedRevenueLow ? null : null, // calcolato sotto
    epsEst,
    epsMom30d: epsMom,
  }
}

// Income statement per growth
export async function getIncomeGrowth(ticker: string) {
  const data = await fmpGet(`income-statement-growth/${ticker}`, { limit: '1' })
  if (!Array.isArray(data) || !data[0]) return null
  const g = data[0]
  return {
    revenueGrowth: g.growthRevenue ? g.growthRevenue * 100 : null,
    epsGrowth:     g.growthEPS     ? g.growthEPS * 100     : null,
  }
}

// Prezzi storici
export async function getHistoricalPrices(ticker: string, from: string, to: string) {
  const data = await fmpGet(`historical-price-full/${ticker}`, { from, to })
  if (!data || !data.historical) return []
  return data.historical.map((d: any) => ({
    date:      d.date,
    open:      d.open,
    high:      d.high,
    low:       d.low,
    close:     d.close,
    adjClose:  d.adjClose,
    volume:    d.volume,
  })).reverse() // FMP restituisce dal più recente al più vecchio
}

// Exchange map FMP: ticker FMP usa suffisso diverso per exchange
// MIL → .MI, XETRA → .DE (o nessuno per DAX), PA → .PA, AS → .AS, MC → .MC
export const FMP_EXCHANGE_SUFFIX: Record<string, string> = {
  MIL:   '.MI',
  XETRA: '.DE',
  PA:    '.PA',
  AS:    '.AS',
  MC:    '.MC',
  BR:    '.BR',
  LS:    '.LS',
  VI:    '.VI',
  HE:    '.HE',
  IR:    '.IR',
  AT:    '.AT',
}

export function toFmpTicker(ticker: string, exchange: string): string {
  const suffix = FMP_EXCHANGE_SUFFIX[exchange] || ''
  return `${ticker}${suffix}`
}
