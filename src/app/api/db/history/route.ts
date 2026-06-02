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
    // Legge con paginazione per bypassare limite 1000 Supabase
    let all: any[] = []
    let from = 0
    const PAGE = 1000

    while (true) {
      const { data, error } = await supabase
        .from('price_history')
        .select('date,close')
        .eq('ticker', ticker)
        .eq('exchange', exchange)
        .order('date', { ascending: true })
        .range(from, from + PAGE - 1)

      if (error) return NextResponse.json({ error: error.message }, { status: 500 })
      if (!data || data.length === 0) break
      all = all.concat(data)
      if (data.length < PAGE) break
      from += PAGE
    }

    if (all.length === 0) {
      return NextResponse.json({ 
        history: [], 
        momentum: { mom1w: null, mom1m: null, mom6m: null, mom12m: null } 
      })
    }

    const history = all.map((d: any) => ({
      date: d.date,
      open: d.close,
      high: d.close,
      low: d.close,
      close: d.close,
      adjusted_close: d.close,
      volume: null,
    }))

    const closes = all.map((d: any) => d.close) as number[]
    const n = closes.length
    const last = closes[n - 1]

    const getMom = (lag: number): number | null => {
      if (n <= lag) return null
      const p = closes[n - 1 - lag]
      return p && p > 0 ? (last / p - 1) * 100 : null
    }

    const momentum = {
      mom1w: getMom(5),
      mom1m: getMom(21),
      mom6m: getMom(131),
      mom12m: getMom(252),
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
