import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 3600

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET(req: NextRequest) {
  const ticker = req.nextUrl.searchParams.get('ticker') || ''
  const exchange = req.nextUrl.searchParams.get('exchange') || ''

  if (!ticker || !exchange) {
    return NextResponse.json({ error: 'Missing params' }, { status: 400 })
  }

  try {
    // Legge tutta la serie storica con paginazione
    let all: any[] = []
    let from = 0
    while (true) {
      const { data, error } = await supabase
        .from('prices_eod')
        .select('date,adj_close')
        .eq('ticker', ticker)
        .eq('exchange', exchange)
        .order('date', { ascending: true })
        .range(from, from + 999)
      if (error || !data || data.length === 0) break
      all = all.concat(data)
      if (data.length < 1000) break
      from += 1000
    }

    if (all.length === 0) {
      return NextResponse.json({
        history: [],
        momentum: { mom1w: null, mom1m: null, mom6m: null, mom12m: null, mom3y: null, mom5y: null }
      })
    }

    const history = all.map((d: any) => ({
      date: d.date,
      open: d.adj_close,
      high: d.adj_close,
      low: d.adj_close,
      close: d.adj_close,
      adjusted_close: d.adj_close,
      volume: null,
    }))

    // Legge momentum da fundamentals — stessa fonte della tabellina
    const { data: fund } = await supabase
      .from('fundamentals')
      .select('mom1w,mom1m,mom6m,mom12m')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .single()

    const momentum = {
      mom1w: fund?.mom1w != null ? fund.mom1w * 100 : null,
      mom1m: fund?.mom1m != null ? fund.mom1m * 100 : null,
      mom6m: fund?.mom6m != null ? fund.mom6m * 100 : null,
      mom12m: fund?.mom12m != null ? fund.mom12m * 100 : null,
      mom3y: null,
      mom5y: null,
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
