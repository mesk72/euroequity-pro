import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 0
export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

function jsonNoCache(body: any, init?: any) {
  const res = NextResponse.json(body, init)
  res.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0')
  res.headers.set('Pragma', 'no-cache')
  res.headers.set('Expires', '0')
  res.headers.set('CDN-Cache-Control', 'no-store')
  res.headers.set('Vercel-CDN-Cache-Control', 'no-store')
  return res
}

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']
const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR']
const FILTER_500M = new Set(['LSE','XETRA','PA','OM','SWX','MIL'])
const TOP_100_EX = new Set(['OB','MC','AS','BR','CPSE','HE','GR'])
const NO_FILTER = new Set(['VI','IR','LS'])
// APAC + North America: top N per market cap, solo titoli con company e sector
const APAC_TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, TSX: 400, ASX: 350, KRX: 400, SGX: 100, US: 2000 }

async function fetchLatestPrices(exchangeList: string[]) {
  // Legge gli ultimi ~6 giorni di prezzi per calcolare prezzo corrente e
  // variazione reale da prices_eod, invece di affidarsi a fundamentals.price
  // / change1d — campi statici aggiornati solo dai run settimanali, causa
  // reale del "prezzo fermo" segnalato su JPM e su tutti gli screener.
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - 6)
  const cutoffStr = cutoff.toISOString().slice(0, 10)

  const byTicker: Record<string, { date: string; adj_close: number }[]> = {}
  for (const exchange of exchangeList) {
    const PAGE = 1000
    let from = 0
    while (true) {
      const { data, error } = await supabase
        .from('prices_eod')
        .select('ticker,date,adj_close')
        .eq('exchange', exchange)
        .gte('date', cutoffStr)
        .order('date', { ascending: false })
        .range(from, from + PAGE - 1)
        .limit(PAGE)
      if (error || !data || data.length === 0) break
      for (const row of data) {
        const key = `${row.ticker}.${exchange}`
        if (!byTicker[key]) byTicker[key] = []
        if (byTicker[key].length < 2) byTicker[key].push({ date: row.date, adj_close: row.adj_close })
      }
      if (data.length < PAGE) break
      from += PAGE
    }
  }

  const result: Record<string, { price: number; date: string; change1d: number | null }> = {}
  for (const key of Object.keys(byTicker)) {
    const rows = byTicker[key]
    if (!rows.length) continue
    const latest = rows[0]
    const prev = rows[1]
    result[key] = {
      price: latest.adj_close,
      date: latest.date,
      change1d: prev && prev.adj_close ? (latest.adj_close / prev.adj_close - 1) : null,
    }
  }
  return result
}

async function fetchAllByExchange(table: string, select: string, exchangeList: string[], universeOnly = false) {
  // Legge un exchange alla volta per evitare il limite di 1000 righe miste
  const all: any[] = []
  for (const exchange of exchangeList) {
    const PAGE = 1000
    let from = 0
    while (true) {
      let query = supabase
        .from(table)
        .select(select)
        .eq('exchange', exchange)
      if (universeOnly) query = query.eq('in_universe', true)
      const { data, error } = await query
        .order('ticker', { ascending: true })
        .range(from, from + PAGE - 1)
        .limit(PAGE)
      if (error || !data || data.length === 0) break
      all.push(...data)
      if (data.length < PAGE) break
      from += PAGE
    }
  }
  return all
}

async function fetchAll(table: string, select: string, exchangeList: string[]) {
  const PAGE = 1000
  let all: any[] = []
  let from = 0
  while (true) {
    const { data, error } = await supabase
      .from(table)
      .select(select)
      .in('exchange', exchangeList)
      .order('ticker', { ascending: true })
      .range(from, from + PAGE - 1)
      .limit(PAGE)
    if (error || !data || data.length === 0) break
    all = all.concat(data)
    if (data.length < PAGE) break
    from += PAGE
  }
  return all
}

function applyUniverseFilter(fundData: any[], stocksData: any[]) {
  // Il filtro universo è già applicato a livello DB tramite in_universe=true
  // Questa funzione ora serve solo per mappare i dati
  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  return stocksData
    .filter(s => fundMap[`${s.ticker}.${s.exchange}`])
    .map(s => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
}

function applyAPACFilter(fundData: any[], stocksData: any[]) {
  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  const TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, ASX: 350, TSX: 400, KRX: 400, SGX: 100, US: 2000 }
  const EXCL_SECTORS = new Set(['71','72','73','74','75','76','77'])

  // Filtra fundData - NON esclude se non in stockMap
  const filtered = fundData.filter(f => {
    if (f.ticker === 'G6M' && f.exchange === 'ASX') return false
    const s = stockMap[`${f.ticker}.${f.exchange}`]
    const sector = s?.sector ?? null
    if (sector && EXCL_SECTORS.has(sector)) return false
    return true
  })

  // Per exchange prendi top N per mktCap
  const byExchange: Record<string, any[]> = {}
  for (const f of filtered) {
    if (!byExchange[f.exchange]) byExchange[f.exchange] = []
    byExchange[f.exchange].push(f)
  }

  const result: any[] = []
  for (const [ex, funds] of Object.entries(byExchange)) {
    const topN = TOP_N[ex] ?? 9999
    const sorted = funds
      .sort((a, b) => (b.mkt_cap ?? 0) - (a.mkt_cap ?? 0))
      .slice(0, topN)
    for (const f of sorted) {
      const s = stockMap[`${f.ticker}.${f.exchange}`] || { ticker: f.ticker, exchange: f.exchange }
      result.push(mapStock(s, f))
    }
  }
  return result
}


export async function GET(req: NextRequest) {
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const exchanges = req.nextUrl.searchParams.get('exchanges') || ''
  const search = req.nextUrl.searchParams.get('search') || ''
  const ticker = req.nextUrl.searchParams.get('ticker') || ''
  const limit = parseInt(req.nextUrl.searchParams.get('limit') || '0')

  try {
    let exList: string[] = []
    if (search || ticker) {
      exList = ALL_RANKED
    } else if (exchange === 'EMU') {
      exList = EMU_EXCHANGES
    } else if (exchange && exchange !== 'EZ' && exchange !== 'ALL') {
      exList = [exchange]
    } else if (exchanges) {
      exList = exchanges.split(',')
    } else {
      exList = ALL_RANKED
    }

    if (ticker && exchange) {
      const [stockRes, fundRes, priceRes, histRes] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,website,price,last_price_date,primary_exchange,description,yahoo_ticker,in_universe').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        supabase.from('fundamentals').select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        // Prezzo reale piu' recente da prices_eod — fundamentals.price e' un
        // campo statico aggiornato solo dagli script weekly, non riflette
        // l'aggiornamento giornaliero. Era la causa del prezzo mostrato
        // fermo di giorni rispetto al dato vero gia' presente nel database.
        supabase.from('prices_eod').select('date,adj_close').eq('ticker', ticker).eq('exchange', exchange).order('date', { ascending: false }).limit(1),
        // Storico ~400 giorni per calcolare il momentum reale (1d/1w/1m/6m/12m)
        // dal prezzo vero, invece che da fundamentals.mom* — stesso problema
        // del prezzo: quei campi restano fermi finche' il run settimanale/
        // notturno non li ricalcola con successo.
        supabase.from('prices_eod').select('date,adj_close').eq('ticker', ticker).eq('exchange', exchange).order('date', { ascending: false }).limit(400),
      ])
      const s: any = stockRes.data?.[0] || {}
      const f: any = fundRes.data?.[0] || {}
      const p: any = priceRes.data?.[0] || {}
      if (!s.ticker) return jsonNoCache({ stocks: [] })
      const mapped = mapStock(s, f)
      if (p.adj_close != null) {
        mapped.price = p.adj_close
        mapped.lastPriceDate = p.date
      }
      const hist: any[] = histRes.data || []
      if (hist.length > 1) {
        const latest = hist[0]
        const prevDay = hist[1]
        const c1d = prevDay && prevDay.adj_close ? (latest.adj_close / prevDay.adj_close - 1) * 100 : null
        if (c1d != null) mapped.change1d = c1d
        // mom1w/mom1m/mom6m/mom12m NON vengono piu' ricalcolati qui — quel blocco
        // duplicato sovrascriveva il valore corretto (decimale) letto da
        // fundamentals con un valore gia' moltiplicato per 100, causando la
        // doppia moltiplicazione mostrata sul sito. mapStock() sopra e' l'unica
        // fonte per il momentum, gia' corretta e verificata.
      }
      return jsonNoCache({ stocks: [mapped], source: 'supabase' })
    }

    if (search) {
      const { data } = await supabase
        .from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,website,primary_exchange')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit > 0 ? limit : 20)
      const stocksData = data || []
      if (!stocksData.length) return jsonNoCache({ stocks: [] })
      const tickers = stocksData.map((s: any) => s.ticker)
      const { data: fundData } = await supabase
        .from('fundamentals')
        .select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf')
        .in('ticker', tickers)
      const fundMap: Record<string, any> = {}
      for (const f of (fundData || [])) fundMap[`${f.ticker}.${f.exchange}`] = f
      const stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
      return jsonNoCache({ stocks, source: 'supabase' })
    }

    const isUSOnly = exList.length === 1 && exList[0] === 'US'

    // Per APAC leggi stocks con limit=5000 per assicurarsi di prendere tutti i record
    const stocksSelect = 'ticker,exchange,isin,company,sector,country,flag,website,primary_exchange,yahoo_ticker'
    const fundSelect = 'ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf'

    const [stocksData, fundData] = await Promise.all([
      fetchAllByExchange('stocks', stocksSelect, exList, true),
      fetchAll('fundamentals', fundSelect, exList),
    ])

    let stocks: any[]
    if (isUSOnly) {
      const fundMap: Record<string, any> = {}
      for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f
      stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
    } else {
      // Unificato su applyUniverseFilter: si fida di in_universe=true, ora
      // affidabile su tutti i continenti grazie alla verifica Leeway
      // aggiunta alla costruzione dell'universo. applyAPACFilter (che
      // ricalcolava il top-N da zero ignorando in_universe, includendo
      // quindi anche titoli ormai esclusi rimasti nei fondamentali) non
      // serve piu' ed era la causa dello scarto tra "US" (corretto) e
      // "North America"/"Asia Pacific" combinati (gonfiati).
      stocks = applyUniverseFilter(fundData, stocksData)
    }
    return jsonNoCache({ stocks, source: 'supabase' })

  } catch (e) {
    return jsonNoCache({ error: 'Database error' }, { status: 500 })
  }
}

function mapStock(s: any, f: any) {
  return {
    ticker: s.ticker ?? f.ticker,
    exchange: s.exchange ?? f.exchange,
    isin: s.isin ?? null,
    company: s.company ?? f.company ?? null,
    inUniverse: s.in_universe ?? null,
    sector: s.sector ?? f.sector ?? null,
    country: s.country ?? null,
    flag: s.flag ?? null,
    website: s.website ?? null,
    price: f.price ?? s.price ?? null,
    change1d: f.change1d ?? null,
    ke: f.ke ?? null,
    impliedGrowth10y: f.implied_growth_10y ?? null,
    epsNtmDcf: f.eps_ntm_dcf ?? null,
    epsFwd24: f.eps_fwd24 ?? null,
    epsFwd36: f.eps_fwd36 ?? null,
    epsGrowth1224m: f.eps_growth_12_24m ?? null,
    epsGrowth2436m: f.eps_growth_24_36m ?? null,
    epsCagr2y: f.eps_cagr_2y ?? null,
    lastPriceDate: s.last_price_date ?? null,
    volume: null,
    mktCap: f.mkt_cap != null ? Math.round(f.mkt_cap / 1000 * 100) / 100 : null,
    peTrail: f.pe_trailing ?? null,
    peFwd: f.pe_forward ?? null,
    pb: f.pb ?? null,
    evEbitda: f.ev_ebitda ?? null,
    roe: f.roe ?? null,
    divYield: f.div_yield ?? null,
    beta: f.beta ?? null,
    epsGrowth: f.eps_growth ?? null,
    revGrowth: f.rev_growth ?? null,
    epsMom30d: null,
    mom1w: f.mom1w ?? null,
    mom1m: f.mom1m ?? null,
    mom6m: f.mom6m ?? null,
    mom12m: f.mom12m ?? null,
    valueScore: f.value_score ?? null,
    growthScore: f.growth_score ?? null,
    combinedRank: f.combined_rank ?? null,
    rankPeLtm: f.rank_pe_ltm ?? null,
    rankPeNtm: f.rank_pe_ntm ?? null,
    rankPb: f.rank_pb ?? null,
    rankEpsGr: f.rank_eps_gr ?? null,
    rankRevGr: f.rank_rev_gr ?? null,
    rankMom6Adj: f.rank_mom6_adj ?? null,
    rankMom12Adj: f.rank_mom12_adj ?? null,
    primaryExchange: s.primary_exchange ?? null,
    yahooTicker: s.yahoo_ticker ?? null,
    description: s.description ?? null,
  }
}

