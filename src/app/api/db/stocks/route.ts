import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Tutti gli exchange nel DB
const ALL_EXCHANGES = [
  'MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT',
  'LSE','AIM','SWX','OM','NGM','OB','CPSE'
]

export async function GET(req: NextRequest) {
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const ticker   = req.nextUrl.searchParams.get('ticker')   || ''
  const search   = req.nextUrl.searchParams.get('search')   || ''
  const limit    = parseInt(req.nextUrl.searchParams.get('limit') || '500')

  try {
    // Query stocks
    let stocksQ = supabase
      .from('stocks')
      .select('ticker,exchange,isin,company,sector,country,flag,currency')

    if (ticker && exchange) {
      // Ricerca singolo titolo
      stocksQ = stocksQ.eq('ticker', ticker).eq('exchange', exchange)
    } else if (exchange && exchange !== 'EZ') {
      stocksQ = stocksQ.eq('exchange', exchange)
    } else if (search) {
      stocksQ = stocksQ.or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit)
    }

    const { data: stocksData, error: stocksErr } = await stocksQ

    if (stocksErr) return NextResponse.json({ error: stocksErr.message }, { status: 500 })
    if (!stocksData?.length) return NextResponse.json({ stocks: [] })

    const exchanges = ticker && exchange
      ? [exchange]
      : exchange && exchange !== 'EZ'
        ? [exchange]
        : ALL_EXCHANGES

    // Prezzi live
    let liveQ = supabase
      .from('prices_live')
      .select('ticker,exchange,price,change_1d,volume,updated_at')
      .in('exchange', exchanges)
    const { data: liveData } = await liveQ

    // Fondamentali con momentum
    let fundQ = supabase
      .from('fundamentals')
      .select(`ticker,exchange,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,
               roe,div_yield,div_payout,beta,eps_growth,rev_growth,
               epsMom30d,mom1w,mom1m,mom6m,mom12m,
               value_score,growth_score,fiscal_month,last_report_date`)
      .in('exchange', exchanges)
    const { data: fundData } = await fundQ

    const liveMap: Record<string, any> = {}
    for (const l of (liveData || [])) {
      liveMap[`${l.ticker}.${l.exchange}`] = l
    }
    const fundMap: Record<string, any> = {}
    for (const f of (fundData || [])) {
      fundMap[`${f.ticker}.${f.exchange}`] = f
    }

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

    return NextResponse.json({ stocks, source: 'supabase' })
  } catch {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
