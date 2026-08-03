import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// FIX 3/8/2026 (sicurezza): questa route gira SUL SERVER e deve usare la
// chiave di servizio, non quella pubblica. La chiave pubblica e'
// estraibile dal browser: finche' le API la usavano, era necessario
// lasciare le tabelle leggibili a chiunque — cioe' l'intero database di
// prezzi e fondamentali era scaricabile da chiunque senza registrarsi.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

function jsonNoCache(data: any, init?: any) {
  const res = NextResponse.json(data, init)
  res.headers.set('Cache-Control', 'no-store')
  return res
}

const NORTH_AMERICA = ['US', 'TSX']
const EUROPE = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE']
const ASIA_PACIFIC = ['TSE','SEHK','ASX','KRX','SGX']

// Restituisce SOLO medie aggregate per settore, su un continente specifico
// — mai dati grezzi dei singoli titoli. Calcolato live ad ogni chiamata,
// quindi riflette sempre l'ultimo aggiornamento degli score, senza bisogno
// di una tabella separata da mantenere sincronizzata.
export async function GET(req: NextRequest) {
  // Stessa verifica reale usata negli altri endpoint stanotte — senza un
  // token valido, nessun dato aggregato viene restituito.
  let verifiedUserId: string | null = null
  const authHeader = req.headers.get('authorization') || ''
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7)
    try {
      const { data: { user: verifiedUser } } = await supabase.auth.getUser(token)
      if (verifiedUser?.id) verifiedUserId = verifiedUser.id
    } catch {}
  }
  if (!verifiedUserId) {
    return jsonNoCache({ continent: '', averages: [] })
  }

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
    const fetchAllPaged = async (table: string, select: string, applySectorFilter: boolean) => {
      let all: any[] = []
      let from = 0
      while (true) {
        let q = supabase.from(table).select(select).in('exchange', exchangeList)
        if (applySectorFilter && sector) q = q.eq('sector', sector)
        if (table === 'stocks') q = q.eq('in_universe', true)
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
    const fundData = await fetchAllPaged('fundamentals', 'ticker, exchange, value_score, growth_score, combined_rank, mkt_cap', false)

    const sectorMap: Record<string, string> = {}
    for (const s of stocksData) sectorMap[`${s.ticker}.${s.exchange}`] = s.sector || 'Unknown'

    const data = fundData
      .map((f: any) => ({ ...f, sector: sectorMap[`${f.ticker}.${f.exchange}`], mktCap: f.mkt_cap || 0 }))
      .filter((f: any) => f.sector && f.mktCap > 0)

    // Aggregazione PESATA PER MARKET CAP (coerente con la pagina Sectors),
    // non media semplice. I dati grezzi per-titolo non escono mai da qui,
    // solo i pesi vengono usati internamente per il calcolo.
    const groups: Record<string, { valueWSum: number; growthWSum: number; rankWSum: number; capSum: number; count: number }> = {}
    for (const row of data) {
      const sec = row.sector
      if (!groups[sec]) groups[sec] = { valueWSum: 0, growthWSum: 0, rankWSum: 0, capSum: 0, count: 0 }
      const w = row.mktCap
      groups[sec].valueWSum += (row.value_score || 0) * w
      groups[sec].growthWSum += (row.growth_score || 0) * w
      groups[sec].rankWSum += (row.combined_rank || 0) * w
      groups[sec].capSum += w
      groups[sec].count += 1
    }

    // Conteggio "universo totale" per settore (in_universe=true, come lo
    // Screener) — separato dal conteggio "con punteggio" usato per la
    // media, cosi' i due numeri non si confondono ma restano entrambi
    // visibili e coerenti con le altre pagine del sito.
    const universeCounts: Record<string, number> = {}
    for (const s of stocksData) {
      const sec = s.sector || 'Unknown'
      universeCounts[sec] = (universeCounts[sec] || 0) + 1
    }

    const result = Object.entries(groups).map(([sec, g]) => ({
      sector: sec,
      avgValueScore: Math.round((g.valueWSum / g.capSum) * 10) / 10,
      avgGrowthScore: Math.round((g.growthWSum / g.capSum) * 10) / 10,
      avgCombinedRank: Math.round((g.rankWSum / g.capSum) * 10) / 10,
      stockCount: g.count,
      universeCount: universeCounts[sec] || g.count,
    }))

    return jsonNoCache({ continent, averages: result })
  } catch (e) {
    return jsonNoCache({ error: 'Server error' }, { status: 500 })
  }
}
