import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

function jsonNoCache(data: any, init?: any) {
  const res = NextResponse.json(data, init)
  res.headers.set('Cache-Control', 'no-store')
  return res
}

const NORTH_AMERICA = ['US', 'TSX']
const EUROPE = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM']
const ASIA_PACIFIC = ['TSE','SEHK','ASX','KRX','SGX']

// Restituisce SOLO medie aggregate per settore, su un continente specifico
// — mai dati grezzi dei singoli titoli. Calcolato live ad ogni chiamata,
// quindi riflette sempre l'ultimo aggiornamento degli score, senza bisogno
// di una tabella separata da mantenere sincronizzata.
export async function GET(req: NextRequest) {
  const continent = req.nextUrl.searchParams.get('continent') || ''
  const sector = req.nextUrl.searchParams.get('sector') || ''

  let exchangeList: string[]
  if (continent === 'north_america') exchangeList = NORTH_AMERICA
  else if (continent === 'europe') exchangeList = EUROPE
  else if (continent === 'asia_pacific') exchangeList = ASIA_PACIFIC
  else return jsonNoCache({ error: 'Invalid continent parameter' }, { status: 400 })

  try {
    // "sector" vive in stocks, i punteggi in fundamentals — servono
    // entrambe le tabelle, unite lato server. Paginazione esplicita:
    // senza, il client si ferma silenziosamente alle prime ~1000 righe,
    // tagliando fuori la maggior parte dei titoli quando il continente
    // ne ha migliaia (bug che causava conteggi sbagliati, es. 85 invece
    // di 373 per Information Technology in Nord America).
    const PAGE = 1000
    async function fetchAllPaged(table: string, select: string, applySectorFilter: boolean) {
      let all: any[] = []
      let from = 0
      while (true) {
        let q = supabase.from(table).select(select).in('exchange', exchangeList)
        if (applySectorFilter && sector) q = q.eq('sector', sector)
        if (table === 'fundamentals') q = q.not('value_score', 'is', null)
        const { data, error } = await q.range(from, from + PAGE - 1)
        if (error || !data || data.length === 0) break
        all = all.concat(data)
        if (data.length < PAGE) break
        from += PAGE
      }
      return all
    }

    const stocksData = await fetchAllPaged('stocks', 'ticker, exchange, sector', true)
    const fundData = await fetchAllPaged('fundamentals', 'ticker, exchange, value_score, growth_score, combined_rank', false)

    const sectorMap: Record<string, string> = {}
    for (const s of stocksData) sectorMap[`${s.ticker}.${s.exchange}`] = s.sector || 'Unknown'

    const data = fundData
      .map((f: any) => ({ ...f, sector: sectorMap[`${f.ticker}.${f.exchange}`] }))
      .filter((f: any) => f.sector)

    // Aggregazione in JS: raggruppa per settore, calcola solo le medie.
    // I dati grezzi per-titolo non escono mai da questa funzione.
    const groups: Record<string, { valueSum: number; growthSum: number; rankSum: number; count: number }> = {}
    for (const row of data) {
      const sec = row.sector || 'Unknown'
      if (!groups[sec]) groups[sec] = { valueSum: 0, growthSum: 0, rankSum: 0, count: 0 }
      groups[sec].valueSum += row.value_score || 0
      groups[sec].growthSum += row.growth_score || 0
      groups[sec].rankSum += row.combined_rank || 0
      groups[sec].count += 1
    }

    const result = Object.entries(groups).map(([sec, g]) => ({
      sector: sec,
      avgValueScore: Math.round((g.valueSum / g.count) * 10) / 10,
      avgGrowthScore: Math.round((g.growthSum / g.count) * 10) / 10,
      avgCombinedRank: Math.round((g.rankSum / g.count) * 10) / 10,
      stockCount: g.count,
    }))

    return jsonNoCache({ continent, averages: result })
  } catch (e) {
    return jsonNoCache({ error: 'Server error' }, { status: 500 })
  }
}
