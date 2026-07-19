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
    // entrambe le tabelle, unite lato server.
    let stocksQuery = supabase
      .from('stocks')
      .select('ticker, exchange, sector')
      .in('exchange', exchangeList)
    if (sector) stocksQuery = stocksQuery.eq('sector', sector)
    const { data: stocksData, error: stocksErr } = await stocksQuery
    if (stocksErr || !stocksData) return jsonNoCache({ error: 'Database error' }, { status: 500 })

    const { data: fundData, error: fundErr } = await supabase
      .from('fundamentals')
      .select('ticker, exchange, value_score, growth_score, combined_rank')
      .in('exchange', exchangeList)
      .not('value_score', 'is', null)
    if (fundErr || !fundData) return jsonNoCache({ error: 'Database error' }, { status: 500 })

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
