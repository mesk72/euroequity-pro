import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT','LSE','AIM','SWX','OM','OB','CPSE','NGM']
const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT']

export async function GET(req: NextRequest) {
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const exchanges = req.nextUrl.searchParams.get('exchanges') || ''
  const search = req.nextUrl.searchParams.get('search') || ''
  const limit = parseInt(req.nextUrl.searchParams.get('limit') || '0')

  try {
    // Determina lista exchange da usare
    let exList: string[] = []
    if (search) {
      exList = ALL_RANKED
    } else if (exchange && exchange !== 'EZ' && exchange !== 'ALL') {
      exList = [exchange]
    } else if (exchange === 'EMU') {
      exList = EMU_EXCHANGES
    } else if (exchanges) {
      exList = exchanges.split(',')
    } else {
      exList = ALL_RANKED
    }

    // Query stocks
    let stocksQ = supabase
      .from('stocks')
      .select('ticker,exchange,isin,company,sector,country,flag')
      .in('exchange', exList)
      .limit(5000)

    if (search) {
      stocksQ = supabase
        .from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit > 0 ? limit : 20)
    }

    const { data: stocksData, error: stocksErr } = await stocksQ
    if (stocksErr) return NextResponse.json({ error: stocksErr.message }, { status: 500 })
    if (!stocksData?.length) return NextResponse.json({ stocks: [] })

    // Query prezzi live
    const { data: liveData } = await supabase
      .from('prices_live')
      .select('ticker,exchange,price,change_1d,volume,updated_at')
      .in('exchange', exList)
      .limit(5000)

    // Query fondamentali
    const { data: fundData } = await supabase
      .from('fundamentals')
      .select('ticker,exchange,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,div_yield,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,change1d')
      .in('exchange', exList)
      .limit(5000)

    // Mappe per accesso rapido
    const liveMap: Record<string, any> = {}
    for (const l of (liveData || [])) {
      liveMap[`${l.ticker}.${l.exchange}`] = l
    }
    const fundMap: Record<string, any> = {}
    for (const f of (fundData || [])) {
      fundMap[`${f.ticker}.${f.exchange}`] = f
    }

    const stocks = stocksData.map(s => {
      const key = `${s.ticker}.${s.exchange}`
      const live = liveMap[key] || {}
      const fund = fundMap[key] || {}
      return {
        ticker: s.ticker,
        exchange: s.exchange,
        isin: s.isin,
        company: s.company,
        sector: s.sector,
        country: s.country,
        flag: s.flag,
        price: live.price ?? null,
        change1d: live.change_1d ?? fund.change1d ?? null,
        volume: live.volume ?? null,
        mktCap: fund.mkt_cap ?? null,
        peTrail: fund.pe_trailing ?? null,
        peFwd: fund.pe_forward ?? null,
        pb: fund.pb ?? null,
        evEbitda: fund.ev_ebitda ?? null,
        roe: fund.roe ?? null,
        divYield: fund.div_yield ?? null,
        beta: fund.beta ?? null,
        epsGrowth: fund.eps_growth ?? null,
        revGrowth: fund.rev_growth ?? null,
        epsMom30d: null,
        mom1w: fund.mom1w ?? null,
        mom1m: fund.mom1m ?? null,
        mom6m: fund.mom6m ?? null,
        mom12m: fund.mom12m ?? null,
        valueScore: fund.value_score ?? null,
        growthScore: fund.growth_score ?? null,
        combinedRank: fund.combined_rank ?? null,
        rankPeLtm: fund.rank_pe_ltm ?? null,
        rankPeNtm: fund.rank_pe_ntm ?? null,
        rankPb: fund.rank_pb ?? null,
        rankEpsGr: fund.rank_eps_gr ?? null,
        rankRevGr: fund.rank_rev_gr ?? null,
      }
    })

    return NextResponse.json({ stocks, source: 'supabase' })
  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
