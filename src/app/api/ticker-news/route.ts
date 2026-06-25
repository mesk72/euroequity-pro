import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'

  let exchanges: string[] = []
  let limit = 500

  if (region === 'americas') {
    exchanges = ['US', 'TSX']  // Canada incluso in Americas
    limit = 500
  } else if (region === 'europe') {
    exchanges = ['PA', 'XETRA', 'MIL', 'MC', 'AS', 'BR', 'LSE', 'SWX', 'OM', 'OB', 'HE', 'IR', 'VI', 'CPSE']
    limit = 600
  } else if (region === 'asia') {
    exchanges = ['TSE', 'SEHK', 'ASX']  // NO TSX - solo Asia Pacific
    limit = 600
  }

  const { data: stocks } = await supabase
    .from('fundamentals')
    .select('ticker, exchange, mkt_cap')
    .in('exchange', exchanges)
    .not('mkt_cap', 'is', null)
    .order('mkt_cap', { ascending: false })
    .limit(limit)

  if (!stocks || stocks.length === 0) return NextResponse.json({ tickers: [] })

  const { data: stockInfo } = await supabase
    .from('stocks')
    .select('ticker, exchange, company')
    .in('exchange', exchanges)
    .in('ticker', (stocks as any[]).map((s: any) => s.ticker))

  const infoMap: Record<string, string> = {}
  for (const s of (stockInfo || [])) {
    if (s.company) infoMap[`${s.ticker}.${s.exchange}`] = s.company
  }

  const tickers = (stocks as any[])
    .map((s: any) => ({
      ticker: s.ticker,
      exchange: s.exchange,
      company: infoMap[`${s.ticker}.${s.exchange}`] || '',
    }))
    .filter((s: any) => s.company.length > 0)

  return NextResponse.json({ tickers })
}
