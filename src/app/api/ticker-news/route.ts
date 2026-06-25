import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const YAHOO_SUFFIX: Record<string, string> = {
  'PA': '.PA', 'XETRA': '.DE', 'MIL': '.MI', 'MC': '.MC',
  'AS': '.AS', 'BR': '.BR', 'LSE': '.L', 'SWX': '.SW',
  'OM': '.ST', 'OB': '.OL', 'HE': '.HE', 'IR': '.IR',
  'VI': '.VI', 'CPSE': '.CO', 'TSE': '.T', 'SEHK': '.HK',
  'ASX': '.AX', 'TSX': '.TO',
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'

  let exchanges: string[] = []
  let limit = 500

  if (region === 'americas') {
    exchanges = ['US', 'TSX']
    limit = 1500
  } else if (region === 'europe') {
    exchanges = ['PA', 'XETRA', 'MIL', 'MC', 'AS', 'BR', 'LSE', 'SWX', 'OM', 'OB', 'HE', 'IR', 'VI', 'CPSE']
    limit = 1500
  } else if (region === 'asia') {
    exchanges = ['TSE', 'SEHK', 'ASX']
    limit = 1500
  }

  // Prendi fundamentals con scores
  const { data: funds } = await supabase
    .from('fundamentals')
    .select('ticker, exchange, mkt_cap, value_score, growth_score, combined_rank')
    .in('exchange', exchanges)
    .not('mkt_cap', 'is', null)
    .order('mkt_cap', { ascending: false })
    .limit(limit)

  if (!funds || funds.length === 0) return NextResponse.json({ tickers: [] })

  const { data: stockInfo } = await supabase
    .from('stocks')
    .select('ticker, exchange, company, yahoo_ticker')
    .in('exchange', exchanges)
    .in('ticker', (funds as any[]).map((s: any) => s.ticker))

  const infoMap: Record<string, { company: string; yahoo_ticker: string | null }> = {}
  for (const s of (stockInfo || [])) {
    if (s.company) infoMap[`${s.ticker}.${s.exchange}`] = {
      company: s.company,
      yahoo_ticker: s.yahoo_ticker || null,
    }
  }

  const tickers = (funds as any[])
    .map((s: any) => {
      const info = infoMap[`${s.ticker}.${s.exchange}`]
      if (!info) return null
      const suffix = YAHOO_SUFFIX[s.exchange] || ''
      const yahooTicker = info.yahoo_ticker || (s.ticker + suffix)
      return {
        ticker: s.ticker,
        exchange: s.exchange,
        company: info.company,
        yahooTicker,
        valueScore: s.value_score,
        growthScore: s.growth_score,
        bestScore: s.combined_rank,
      }
    })
    .filter(Boolean)

  return NextResponse.json({ tickers })
}
