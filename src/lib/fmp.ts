/**
 * FMP (Financial Modeling Prep) API client
 * Documentazione: https://financialmodelingprep.com/developer/docs
 */

const FMP_BASE = 'https://financialmodelingprep.com/api/v3'
const FMP_KEY  = process.env.FMP_KEY || ''

async function fmpGet(endpoint: string, params: Record<string, string> = {}) {
  const url = new URL(`${FMP_BASE}/${endpoint}`)
  url.searchParams.set('apikey', FMP_KEY)
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v)
  try {
    const r = await fetch(url.toString(), { cache: 'no-store' })
    if (!r.ok) return null
    return r.json()
  } catch { return null }
}

function n(val: any): number | null {
  const v = parseFloat(val)
  return isNaN(v) || !isFinite(v) ? null : v
}

export const FMP_EXCHANGE_SUFFIX: Record<string, string> = {
  MIL:'.MI', XETRA:'.DE', PA:'.PA', AS:'.AS', MC:'.MC',
  BR:'.BR',  LS:'.LS',    VI:'.VI', HE:'.HE', IR:'.IR', AT:'.AT',
}

export function toFmpTicker(ticker: string, exchange: string): string {
  return `${ticker}${FMP_EXCHANGE_SUFFIX[exchange] || ''}`
}

function parseFiscalMonth(fiscalYearEnd: string | null): number {
  if (!fiscalYearEnd) return 12
  const m: Record<string,number> = {
    january:1,february:2,march:3,april:4,may:5,june:6,
    july:7,august:8,september:9,october:10,november:11,december:12
  }
  return m[fiscalYearEnd.toLowerCase()] || 12
}

export async function getBulkQuotes(fmpTickers: string[]) {
  if (!fmpTickers.length) return []
  const data = await fmpGet(`quote/${fmpTickers.join(',')}`)
  if (!Array.isArray(data)) return []
  return data.map((q: any) => ({
    fmpSymbol: q.symbol, price: n(q.price),
    change1d: n(q.changesPercentage), changeAbs: n(q.change),
    volume: q.volume ? parseInt(q.volume) : null,
    mktCap: q.marketCap ? n(q.marketCap)! / 1e9 : null,
    prevClose: n(q.previousClose),
  }))
}

export async function getProfile(fmpTicker: string) {
  const data = await fmpGet(`profile/${fmpTicker}`)
  if (!Array.isArray(data) || !data[0]) return null
  const p = data[0]
  return {
    company: p.companyName, sector: p.sector, isin: p.isin,
    website: p.website, mktCap: p.mktCap ? n(p.mktCap)! / 1e9 : null,
    beta: n(p.beta), fiscalMonth: parseFiscalMonth(p.fiscalYearEnd),
  }
}

export async function getAnalystEstimates(fmpTicker: string) {
  const data = await fmpGet(`analyst-estimates/${fmpTicker}`, { limit: '4' })
  if (!Array.isArray(data) || !data[0]) return null
  const [e0, e1, e2] = data
  return {
    eps_fy1: n(e0?.estimatedEpsAvg),     eps_fy2: n(e1?.estimatedEpsAvg),
    rev_fy1: n(e0?.estimatedRevenueAvg), rev_fy2: n(e1?.estimatedRevenueAvg),
    eps_fy1_30d: n(e1?.estimatedEpsAvg), eps_fy2_30d: n(e2?.estimatedEpsAvg),
    rev_fy1_30d: n(e1?.estimatedRevenueAvg), rev_fy2_30d: n(e2?.estimatedRevenueAvg),
    lastUpdated: e0?.date || null,
  }
}

export async function getIncomeStatement(fmpTicker: string) {
  const data = await fmpGet(`income-statement/${fmpTicker}`, { limit:'2', period:'annual' })
  if (!Array.isArray(data) || !data[0]) return null
  const last = data[0]
  return {
    eps_fy0: n(last.eps),
    rev_fy0: last.revenue ? n(last.revenue)! / 1e6 : null,
    lastReportDate: last.date,
  }
}

export async function getKeyMetrics(fmpTicker: string) {
  const data = await fmpGet(`key-metrics-ttm/${fmpTicker}`)
  if (!Array.isArray(data) || !data[0]) return null
  const m = data[0]
  return {
    pb:        n(m.pbRatioTTM),
    evEbitda:  n(m.enterpriseValueOverEBITDATTM),
    roe:       m.roeTTM            ? n(m.roeTTM)! * 100            : null,
    roa:       m.roaTTM            ? n(m.roaTTM)! * 100            : null,
    netMargin: m.netProfitMarginTTM ? n(m.netProfitMarginTTM)! * 100 : null,
    divYield:  m.dividendYieldTTM   ? n(m.dividendYieldTTM)! * 100   : null,
    divPayout: m.payoutRatioTTM     ? n(m.payoutRatioTTM)! * 100     : null,
  }
}

export async function getHistoricalPrices(fmpTicker: string, from: string, to: string) {
  const data = await fmpGet(`historical-price-full/${fmpTicker}`, { from, to })
  if (!data?.historical) return []
  return [...data.historical].reverse().map((d: any) => ({
    date: d.date, open: n(d.open), high: n(d.high), low: n(d.low),
    close: n(d.close), adjClose: n(d.adjClose) ?? n(d.close),
    volume: d.volume ? parseInt(d.volume) : null,
  }))
}

export async function getFullFundamentals(fmpTicker: string) {
  const [profile, income, estimates, metrics] = await Promise.all([
    getProfile(fmpTicker), getIncomeStatement(fmpTicker),
    getAnalystEstimates(fmpTicker), getKeyMetrics(fmpTicker),
  ])
  return {
    company: profile?.company || null, sector: profile?.sector || null,
    isin: profile?.isin || null, mktCap: profile?.mktCap || null,
    beta: profile?.beta || null, fiscalMonth: profile?.fiscalMonth || 12,
    eps_fy0: income?.eps_fy0 || null, rev_fy0: income?.rev_fy0 || null,
    lastReportDate: income?.lastReportDate || null,
    eps_fy1: estimates?.eps_fy1 || null, eps_fy2: estimates?.eps_fy2 || null,
    rev_fy1: estimates?.rev_fy1 || null, rev_fy2: estimates?.rev_fy2 || null,
    eps_fy1_30d: estimates?.eps_fy1_30d || null, eps_fy2_30d: estimates?.eps_fy2_30d || null,
    rev_fy1_30d: estimates?.rev_fy1_30d || null, rev_fy2_30d: estimates?.rev_fy2_30d || null,
    pb: metrics?.pb || null, evEbitda: metrics?.evEbitda || null,
    roe: metrics?.roe || null, roa: metrics?.roa || null,
    netMargin: metrics?.netMargin || null,
    divYield: metrics?.divYield || null, divPayout: metrics?.divPayout || null,
  }
}
