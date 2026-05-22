import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { unstable_cache } from 'next/cache'

// Revalidate ogni 60 secondi
export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_EXCHANGES = [
  'MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT',
  'LSE','AIM','SWX','OM','NGM','OB','CPSE'
]
const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT']
const FUND_SELECT   = 'ticker,exchange,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,div_payout,beta,eps_growth,rev_growth,mom1w,mom1m,mom6m,mom12m,value_score,growth_score'

async function fetchPaged(table: string, select: string, exList: string[]) {
  const all: any[] = []
  let from = 0
  while (true) {
    const { data, error } = await supabase
      .from(table).select(select)
      .in('exchange', exList)
      .range(from, from + 999)
    if (error || !data?.length) break
    all.push(...data)
    if (data.length < 1000) break
    from += 1000
  }
  return all
}

// Cache per ogni exchange key — 60 secondi
const getExchangeData = unstable_cache(
  async (exKey: string, exList: string[]) => {
    const [stocks, live, fund] = await Promise.all([
      fetchPaged('stocks', 'ticker,exchange,isin,company,sector,country,flag,currency', exList),
      fetchPaged('prices_live', 'ticker,exchange,price,change_1d,volume', exList),
      fetchPaged('fundamentals', FUND_SELECT, exList),
    ])
    return { stocks, live, fund }
  },
  ['exchange-data'],
  { revalidate: 60 }
)

function buildStocks(stocksData: any[], liveData: any[], fundData: any[]) {
  const liveMap: Record<string, any> = {}
  for (const l of liveData) liveMap[`${l.ticker}.${l.exchange}`] = l

  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  return stocksData.map(s => {
    const key  = `${s.ticker}.${s.exchange}`
    const live = liveMap[key] || {}
    const fund = fundMap[key] || {}
    return {
      ticker:      s.ticker,
      exchange:    s.exchange,
      isin:        s.isin      || null,
      company:     s.company   || null,
      sector:      s.sector    || null,
      country:     s.country   || null,
      flag:        s.flag      || '',
      currency:    s.currency  || 'EUR',
      price:       live.price       ?? null,
      change1d:    live.change_1d   ?? null,
      volume:      live.volume      ?? null,
      mktCap:      fund.mkt_cap     ?? null,
      peTrail:     fund.pe_trailing ?? null,
      peFwd:       fund.pe_forward  ?? null,
      pb:          fund.pb          ?? null,
      evEbitda:    fund.ev_ebitda   ?? null,
      roe:         fund.roe         ?? null,
      divYield:    fund.div_yield   ?? null,
      divPayout:   fund.div_payout  ?? null,
      beta:        fund.beta        ?? null,
      epsGrowth:   fund.eps_growth  ?? null,
      revGrowth:   fund.rev_growth  ?? null,
      epsMom30d:   null,
      mom1w:       fund.mom1w       ?? null,
      mom1m:       fund.mom1m       ?? null,
      mom6m:       fund.mom6m       ?? null,
      mom12m:      fund.mom12m      ?? null,
      valueScore:  fund.value_score  ?? null,
      growthScore: fund.growth_score ?? null,
    }
  })
}

export async function GET(req: NextRequest) {
  const exchange       = req.nextUrl.searchParams.get('exchange')  || ''
  const exchangesParam = req.nextUrl.searchParams.get('exchanges') || ''
  const ticker         = req.nextUrl.searchParams.get('ticker')    || ''
  const search         = req.nextUrl.searchParams.get('search')    || ''

  try {
    // Ricerca singolo titolo — no cache
    if (ticker && exchange) {
      const [s, l, f] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,currency')
          .eq('ticker', ticker).eq('exchange', exchange),
        supabase.from('prices_live').select('ticker,exchange,price,change_1d,volume')
          .eq('ticker', ticker).eq('exchange', exchange),
        supabase.from('fundamentals').select(FUND_SELECT)
          .eq('ticker', ticker).eq('exchange', exchange),
      ])
      const stocks = buildStocks(s.data || [], l.data || [], f.data || [])
      return NextResponse.json({ stocks, total: stocks.length })
    }

    // Ricerca testuale — no cache
    if (search) {
      const exList = exchangesParam ? exchangesParam.split(',') : ALL_EXCHANGES
      const { data } = await supabase.from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,currency')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .in('exchange', exList).limit(20)
      const tickers = (data || []).map((s: any) => s.ticker)
      if (!tickers.length) return NextResponse.json({ stocks: [] })
      const [l, f] = await Promise.all([
        supabase.from('prices_live').select('ticker,exchange,price,change_1d,volume').in('ticker', tickers),
        supabase.from('fundamentals').select(FUND_SELECT).in('ticker', tickers),
      ])
      const stocks = buildStocks(data || [], l.data || [], f.data || [])
      return NextResponse.json({ stocks, total: stocks.length })
    }

    // Query per exchange — con cache
    let exList: string[]
    let exKey: string

    if (exchangesParam) {
      exList = exchangesParam.split(',')
      exKey  = exList.sort().join(',')
    } else if (exchange === 'EMU') {
      exList = EMU_EXCHANGES
      exKey  = 'EMU'
    } else if (exchange && exchange !== 'EZ') {
      exList = [exchange]
      exKey  = exchange
    } else {
      exList = ALL_EXCHANGES
      exKey  = 'ALL'
    }

    const { stocks: stocksData, live: liveData, fund: fundData } =
      await getExchangeData(exKey, exList)

    const stocks = buildStocks(stocksData, liveData, fundData)
    return NextResponse.json({ stocks, total: stocks.length })

  } catch (e: any) {
    console.error('stocks API error:', e)
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
