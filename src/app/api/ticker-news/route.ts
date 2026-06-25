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

async function fetchAll(exchanges: string[], limit: number) {
  // Supabase ha limite 1000 per query - facciamo più query
  const all: any[] = []
  const pageSize = 1000
  let offset = 0
  while (all.length < limit) {
    const { data } = await supabase
      .from('fundamentals')
      .select('ticker, exchange, mkt_cap, value_score, growth_score, combined_rank')
      .in('exchange', exchanges)
      .not('mkt_cap', 'is', null)
      .order('mkt_cap', { ascending: false })
      .range(offset, offset + pageSize - 1)
    if (!data || data.length === 0) break
    all.push(...data)
    if (data.length < pageSize) break
    offset += pageSize
  }
  return all.slice(0, limit)
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'

  let exchanges: string[] = []
  let limit = 1500

  if (region === 'americas') {
    exchanges = ['US', 'TSX']
  } else if (region === 'europe') {
    exchanges = ['PA', 'XETRA', 'MIL', 'MC', 'AS', 'BR', 'LSE', 'SWX', 'OM', 'OB', 'HE', 'IR', 'VI', 'CPSE']
  } else if (region === 'asia') {
    exchanges = ['TSE', 'SEHK', 'ASX']
  }

  const funds = await fetchAll(exchanges, limit)
  if (funds.length === 0) return NextResponse.json({ tickers: [] })

  // Prendi info stocks in batch da 1000
  const allInfo: any[] = []
  const tickers = funds.map((s: any) => s.ticker)
  for (let i = 0; i < tickers.length; i += 1000) {
    const { data } = await supabase
      .from('stocks')
      .select('ticker, exchange, company, yahoo_ticker')
      .in('exchange', exchanges)
      .in('ticker', tickers.slice(i, i + 1000))
    if (data) allInfo.push(...data)
  }

  const infoMap: Record<string, { company: string; yahoo_ticker: string | null }> = {}
  for (const s of allInfo) {
    if (s.company) infoMap[`${s.ticker}.${s.exchange}`] = {
      company: s.company,
      yahoo_ticker: s.yahoo_ticker || null,
    }
  }

  const result = funds
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

  return NextResponse.json({ tickers: result })
}
