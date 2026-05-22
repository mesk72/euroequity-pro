import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 30

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_EXCHANGES = [
  'MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT',
  'LSE','AIM','SWX','OM','NGM','OB','CPSE'
]

const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT']

const FUND_SELECT = 'ticker,exchange,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,div_payout,beta,eps_growth,rev_growth,mom1w,mom1m,mom6m,mom12m,value_score,growth_score'

async function fetchPaged(table: string, select: string, exList: string[]) {
  const all: any[] = []
  let from = 0
  const size = 1000
  while (true) {
    const { data, error } = await supabase
      .from(table).select(select)
      .in('exchange', exList)
      .range(from, from + size - 1)
    if (error || !data?.length) break
    all.push(...data)
    if (data.length < size) break
    from += size
  }
  return all
}

export async function GET(req: NextRequest) {
  const exchange      = req.nextUrl.searchParams.get('exchange')  || ''
  const exchangesParam= req.nextUrl.searchParams.get('exchanges') || ''
  const ticker        = req.nextUrl.searchParams.get('ticker')    || ''
  const search        = req.nextUrl.searchParams.get('search')    || ''

  try {
    // Determina lista exchange
    let exList: string[]
    if (ticker && exchange) {
      exList = [exchange]
    } else if (exchangesParam) {
      exList = exchangesParam.split(',')
    } else if (exchange === 'EMU') {
      exList = EMU_EXCHANGES
    } else if (exchange && exchange !== 'EZ') {
      exList = [exchange]
    } else {
      exList = ALL_EXCHANGES
    }

    // Stocks
    let stocksData: any[] = []
    if (ticker && exchange) {
      const { data } = await supabase.from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,currency')
        .eq('ticker', ticker).eq('exchange', exchange)
      stocksData = data || []
    } else if (search) {
      const { data } = await supabase.from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,currency')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .in('exchange', exList).limit(20)
      stocksData = data || []
    } else {
      stocksData = await fetchPaged('stocks',
        'ticker,exchange,isin,company,sector,country,flag,currency', exList)
    }

    if (!stocksData.length) return NextResponse.json({ stocks: [] })

    // Prezzi live e fondamentali in parallelo
    const [liveData, fundData] = await Promise.all([
      fetchPaged('prices_live', 'ticker,exchange,price,change_1d,volume', exList),
      fetchPaged('fundamentals', FUND_SELECT, exList),
    ])

    const liveMap: Record<string, any> = {}
    for (const l of liveData) liveMap[`${l.ticker}.${l.exchange}`] = l

    const fundMap: Record<string, any> = {}
    for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

    const stocks = stocksData.map(s => {
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
        price:       live.price      ?? null,
        change1d:    live.change_1d  ?? null,
        volume:      live.volume     ?? null,
        mktCap:      fund.mkt_cap    ?? null,
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

    return NextResponse.json({ stocks, total: stocks.length })
  } catch (e: any) {
    console.error('stocks API error:', e)
    return NextResponse.json({ error: 'Database error', detail: e?.message }, { status: 500 })
  }
}
