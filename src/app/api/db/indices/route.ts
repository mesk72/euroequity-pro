import { NextResponse } from 'next/server'

export const revalidate = 60

const EODHD_KEY = process.env.EODHD_KEY || ''

const INDICES = [
  { name: 'STOXX 600',      ticker: 'SXXP.INDX',    source: 'eodhd', flag: '🌍' },
  { name: 'Euro Stoxx 50',  ticker: 'STOXX50E.INDX', source: 'eodhd', flag: '🇪🇺' },
  { name: 'FTSE MIB',       ticker: 'FTSEMIB.MI',    source: 'yahoo', flag: '🇮🇹' },
  { name: 'DAX',            ticker: 'GDAXI.INDX',    source: 'eodhd', flag: '🇩🇪' },
  { name: 'CAC 40',         ticker: 'FCHI.INDX',     source: 'eodhd', flag: '🇫🇷' },
  { name: 'IBEX 35',        ticker: 'IBEX.INDX',     source: 'eodhd', flag: '🇪🇸' },
  { name: 'AEX',            ticker: 'AEX.INDX',      source: 'eodhd', flag: '🇳🇱' },
  { name: 'BEL 20',         ticker: 'BFX.INDX',      source: 'eodhd', flag: '🇧🇪' },
  { name: 'ATX',            ticker: 'ATX.INDX',      source: 'eodhd', flag: '🇦🇹' },
  { name: 'OMX Helsinki',   ticker: 'OMXHPI.INDX',   source: 'eodhd', flag: '🇫🇮' },
  { name: 'PSI 20',         ticker: 'PSI20.INDX',    source: 'eodhd', flag: '🇵🇹' },
  { name: 'FTSE 100',       ticker: '^FTSE',          source: 'yahoo', flag: '🇬🇧' },
  { name: 'SMI',            ticker: 'SSMI.INDX',     source: 'eodhd', flag: '🇨🇭' },
  { name: 'OMX Stockholm',  ticker: 'OMXS30.INDX',   source: 'eodhd', flag: '🇸🇪' },
  { name: 'OBX',            ticker: 'OBX.OL',        source: 'eodhd', flag: '🇳🇴' },
  { name: 'OMX Copenhagen', ticker: 'OMXC25.INDX',   source: 'eodhd', flag: '🇩🇰' },
]

async function fetchEodhd(ticker: string) {
  try {
    const url = `https://eodhd.com/api/real-time/${ticker}?api_token=${EODHD_KEY}&fmt=json`
    const r = await fetch(url, { next: { revalidate: 60 } })
    if (!r.ok) return null
    const d = await r.json()
    const close = d.close !== 'NA' ? parseFloat(d.close) : parseFloat(d.previousClose)
    const changeP = d.change_p !== 'NA' ? parseFloat(d.change_p) : null
    if (!close || isNaN(close)) return null
    return { close, changeP }
  } catch { return null }
}

async function fetchYahoo(ticker: string) {
  try {
    const encoded = encodeURIComponent(ticker)
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?interval=1d&range=5d`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      next: { revalidate: 60 }
    })
    if (!r.ok) return null
    const d = await r.json()
    const result = d?.chart?.result?.[0]
    if (!result) return null
    const closes = result.indicators?.quote?.[0]?.close?.filter((v: any) => v != null) || []
    if (closes.length < 2) return null
    const close   = closes[closes.length - 1]
    const prev    = closes[closes.length - 2]
    const changeP = prev ? parseFloat(((close / prev - 1) * 100).toFixed(2)) : null
    return { close: parseFloat(close.toFixed(2)), changeP }
  } catch { return null }
}

export async function GET() {
  try {
    const results = await Promise.all(
      INDICES.map(async (idx) => {
        const data = idx.source === 'yahoo'
          ? await fetchYahoo(idx.ticker)
          : await fetchEodhd(idx.ticker)
        return {
          ticker:  idx.ticker,
          name:    idx.name,
          flag:    idx.flag,
          close:   data?.close   ?? null,
          changeP: data?.changeP ?? null,
        }
      })
    )
    return NextResponse.json({ indices: results })
  } catch {
    return NextResponse.json({ indices: [] })
  }
}
