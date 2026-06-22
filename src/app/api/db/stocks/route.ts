import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','US']
const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR']
const FILTER_500M = new Set(['LSE','XETRA','PA','OM','SWX','MIL'])
const TOP_100_EX = new Set(['OB','MC','AS','BR','CPSE','HE','GR'])
const NO_FILTER = new Set(['VI','IR','LS'])
// APAC + North America: top N per market cap, solo titoli con company e sector
const APAC_TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, TSX: 400, ASX: 350, US: 2000 }

async function fetchAll(table: string, select: string, exchangeList: string[]) {
  const PAGE = 1000
  let all: any[] = []
  let from = 0
  while (true) {
    const { data, error } = await supabase
      .from(table)
      .select(select)
      .in('exchange', exchangeList)
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
  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  const filtered = fundData.filter(f => {
    if (!stockMap[`${f.ticker}.${f.exchange}`]) return false
    const mktCap = f.mkt_cap ?? null
    if (NO_FILTER.has(f.exchange)) return true
    if (TOP_100_EX.has(f.exchange)) return true
    if (FILTER_500M.has(f.exchange)) return mktCap != null && mktCap >= 500
    return true
  }).map(f => stockMap[`${f.ticker}.${f.exchange}`])

  const top100Map: Record<string, any[]> = {}
  filtered.forEach(s => {
    if (s && TOP_100_EX.has(s.exchange)) {
      if (!top100Map[s.exchange]) top100Map[s.exchange] = []
      const f = fundMap[`${s.ticker}.${s.exchange}`] || {}
      top100Map[s.exchange].push({ ...s, _mktCap: f.mkt_cap ?? 0 })
    }
  })
  Object.keys(top100Map).forEach(ex => {
    top100Map[ex].sort((a,b) => b._mktCap - a._mktCap)
    top100Map[ex] = top100Map[ex].slice(0,100)
  })
  const top100Set = new Set(Object.values(top100Map).flat().map((s:any) => `${s.ticker}.${s.exchange}`))

  const result = filtered.filter(s =>
    !TOP_100_EX.has(s.exchange) || top100Set.has(`${s.ticker}.${s.exchange}`)
  )

  return result.map(s => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
}


function applyAPACFilter(fundData: any[], stocksData: any[]) {
  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  // Top N per exchange ordinati per mktCap
  const TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, ASX: 350, TSX: 400, US: 2000 }
  const EXCL_SECTORS = new Set(['71','72','73','74','75','76','77'])

  const byExchange: Record<string, any[]> = {}
  for (const f of fundData) {
    const s = stockMap[`${f.ticker}.${f.exchange}`] || {}
    const sector = s.sector ?? null
    if (sector && EXCL_SECTORS.has(sector)) continue
    if (f.ticker === 'G6M' && f.exchange === 'ASX') continue
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
      const s = stockMap[`${f.ticker}.${f.exchange}`]
      if (s) {
        result.push(mapStock(s, f))
      } else {
        // ticker non in stocks - usa solo i dati di fundamentals
        result.push(mapStock({ ticker: f.ticker, exchange: f.exchange }, f))
      }
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
      const [stockRes, fundRes] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,website,price,last_price_date,primary_exchange,description,yahoo_ticker').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        supabase.from('fundamentals').select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj').eq('ticker', ticker).eq('exchange', exchange).limit(1),
      ])
      const s: any = stockRes.data?.[0] || {}
      const f: any = fundRes.data?.[0] || {}
      if (!s.ticker) return NextResponse.json({ stocks: [] })
      return NextResponse.json({ stocks: [mapStock(s, f)], source: 'supabase' })
    }

    if (search) {
      const { data } = await supabase
        .from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,website,primary_exchange')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit > 0 ? limit : 20)
      const stocksData = data || []
      if (!stocksData.length) return NextResponse.json({ stocks: [] })
      const tickers = stocksData.map((s: any) => s.ticker)
      const { data: fundData } = await supabase
        .from('fundamentals')
        .select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj')
        .in('ticker', tickers)
      const fundMap: Record<string, any> = {}
      for (const f of (fundData || [])) fundMap[`${f.ticker}.${f.exchange}`] = f
      const stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
      return NextResponse.json({ stocks, source: 'supabase' })
    }

    const APAC_EX = new Set(['TSE','SEHK','TSX','ASX'])
    const isUSOnly = exList.length === 1 && exList[0] === 'US'
    const hasAPAC = exList.some(e => APAC_EX.has(e))
    const isMultiNorthAmerica = exList.includes('US') && exList.includes('TSX') && exList.length === 2

    // Per APAC leggi stocks con limit=5000 per assicurarsi di prendere tutti i record
    const stocksSelect = 'ticker,exchange,isin,company,sector,country,flag,website,primary_exchange,yahoo_ticker'
    const fundSelect = 'ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj'

    const [stocksData, fundData] = await Promise.all([
      fetchAll('stocks', stocksSelect, exList),
      fetchAll('fundamentals', fundSelect, exList),
    ])

    let stocks: any[]
    if (isUSOnly) {
      const fundMap: Record<string, any> = {}
      for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f
      stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
    } else if (hasAPAC || isMultiNorthAmerica) {
      stocks = applyAPACFilter(fundData, stocksData)
    } else {
      stocks = applyUniverseFilter(fundData, stocksData)
    }
    return NextResponse.json({ stocks, source: 'supabase' })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}

function mapStock(s: any, f: any) {
  return {
    ticker: s.ticker ?? f.ticker,
    exchange: s.exchange ?? f.exchange,
    isin: s.isin ?? null,
    company: s.company ?? f.company ?? null,
    sector: s.sector ?? f.sector ?? null,
    country: s.country ?? null,
    flag: s.flag ?? null,
    website: s.website ?? null,
    price: ['TSE','SEHK','TSX','ASX'].includes(s.exchange)
      ? (f.price ?? null)
      : (s.price ?? f.price ?? null),
    change1d: f.change1d ?? null,
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

