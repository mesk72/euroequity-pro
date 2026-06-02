import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT','LSE','AIM','SWX','OM','OB','CPSE','NGM']
const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT']

// Paginazione per bypassare limite 1000 Supabase
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
    if (error || !data || data.length === 0) break
    all = all.concat(data)
    if (data.length < PAGE) break
    from += PAGE
  }
  return all
}

export async function GET(req: NextRequest) {
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const exchanges = req.nextUrl.searchParams.get('exchanges') || ''
  const search = req.nextUrl.searchParams.get('search') || ''
  const ticker = req.nextUrl.searchParams.get('ticker') || ''
  const limit = parseInt(req.nextUrl.searchParams.get('limit') || '0')

  try {
    // Determina lista exchange
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

    // Ticker singolo — query diretta
    if (ticker && exchange) {
      const [stockRes, fundRes] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,website').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        supabase.from('fundamentals').select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m').eq('ticker', ticker).eq('exchange', exchange).limit(1),
      ])
      const s = stockRes.data?.[0] || {}
      const f: any = fundRes.data?.[0] || {}
      if (!s.ticker) return NextResponse.json({ stocks: [] })
      return NextResponse.json({ stocks: [mapStock(s, f)], source: 'supabase' })
    }

    // Search
    if (search) {
      const { data } = await supabase
        .from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,website')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit > 0 ? limit : 20)
      const stocksData = data || []
      if (!stocksData.length) return NextResponse.json({ stocks: [] })
      const tickers = stocksData.map((s: any) => s.ticker)
      const { data: fundData } = await supabase
        .from('fundamentals')
        .select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m')
        .in('ticker', tickers)
      const fundMap: Record<string, any> = {}
      for (const f of (fundData || [])) fundMap[`${f.ticker}.${f.exchange}`] = f
      const stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
      return NextResponse.json({ stocks, source: 'supabase' })
    }

    // Lista completa con paginazione
    const [stocksData, fundData] = await Promise.all([
      fetchAll('stocks', 'ticker,exchange,isin,company,sector,country,flag,website', exList),
      fetchAll('fundamentals', 'ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m', exList),
    ])

    const fundMap: Record<string, any> = {}
    for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

    const stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
    return NextResponse.json({ stocks, source: 'supabase' })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}

function mapStock(s: any, f: any) {
  return {
    ticker: s.ticker,
    exchange: s.exchange,
    isin: s.isin ?? null,
    company: s.company ?? null,
    sector: s.sector ?? null,
    country: s.country ?? null,
    flag: s.flag ?? null,
    website: s.website ?? null,
    price: f.price ?? null,
    change1d: f.change1d ?? null,
    volume: null,
    mktCap: f.mkt_cap ?? null,
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
  }
}
