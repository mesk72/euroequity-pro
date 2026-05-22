import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_EXCHANGES = [
  'MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT',
  'LSE','AIM','SWX','OM','NGM','OB','CPSE'
]

async function fetchAllPaged(table: string, selectStr: string, exchangeFilter: string[]) {
  const results: any[] = []
  let from = 0
  const pageSize = 1000
  while (true) {
    const { data, error } = await supabase
      .from(table)
      .select(selectStr)
      .in('exchange', exchangeFilter)
      .range(from, from + pageSize - 1)
    if (error || !data?.length) break
    results.push(...data)
    if (data.length < pageSize) break
    from += pageSize
  }
  return results
}

export async function GET(req: NextRequest) {
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const ticker   = req.nextUrl.searchParams.get('ticker')   || ''
  const search   = req.nextUrl.searchParams.get('search')   || ''
  const limit    = parseInt(req.nextUrl.searchParams.get('limit') || '1000')

  try {
    const exchanges = (exchange && exchange !== 'EZ')
      ? [exchange]
      : ALL_EXCHANGES

    // Query stocks
    let stocksQ = supabase
      .from('stocks')
      .select('ticker,exchange,isin,company,sector,country,flag,currency')

    if (ticker && exchange) {
      stocksQ = stocksQ.eq('ticker', ticker).eq('exchange', exchange)
    } else if (search) {
      stocksQ = stocksQ
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .in('exchange', exchanges)
        .limit(limit)
    } else {
      stocksQ = stocksQ.in('exchange', exchanges)
    }

    // Paginazione per stocks
    let stocksData: any[] = []
    if (ticker && exchange) {
      const { data } = await stocksQ
      stocksData = data || []
    } else if (search) {
      const { data } = await stocksQ
      stocksData = data || []
    } else {
      stocksData = await fetchAllPaged(
        'stocks',
        'ticker,exchange,isin,company,sector,country,flag,currency',
        exchanges
      )
    }

    if (!stocksData.length) return NextResponse.json({ stocks: [] })

    // Prezzi live — paginati
    const liveData = await fetchAllPaged(
      'prices_live',
      'ticker,exchange,price,change_1d,volume',
      exchanges
    )

    // Fondamentali — paginati
    const fundData = await fetchAllPaged(
      'fundamentals',
      'ticker,exchange,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,div_payout,beta,eps_growth,rev_growth,epsMom30d,mom1w,mom1m,mom6m,mom12m,value_score,growth_score',
      exchanges
    )

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
        isin:        s.isin,
        company:     s.company,
        sector:      s.sector,
        country:     s.country,
        flag:        s.flag,
        currency:    s.currency || 'EUR',
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
        epsMom30d:   fund.epsMom30d   ?? null,
        mom1w:       fund.mom1w       ?? null,
        mom1m:       fund.mom1m       ?? null,
        mom6m:       fund.mom6m       ?? null,
        mom12m:      fund.mom12m      ?? null,
        valueScore:  fund.value_score  ?? null,
        growthScore: fund.growth_score ?? null,
      }
    })

    return NextResponse.json({ stocks, total: stocks.length, source: 'supabase' })
  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
