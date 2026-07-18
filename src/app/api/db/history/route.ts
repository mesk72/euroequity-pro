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

    // Calcola TUTTI i momentum da prices_eod — fonte unica
    // FIX: usa giorni di TRADING (indici fissi), non giorni di calendario,
    // per allinearsi esattamente alla convenzione ForwardAlpha standard
    // gia' usata per il valore salvato in fundamentals (1w=5, 1m=21, 6m=127, 12m=253 trading days).
    const closes = all.map((d: any) => d.adj_close) as number[]
    const lastPrice = closes[closes.length - 1]

    const momBack = (tradingDaysBack: number): number | null => {
      const idx = closes.length - 1 - tradingDaysBack
      if (idx < 0) return null
      const p = closes[idx]
      return p && p > 0 ? (lastPrice / p - 1) * 100 : null
    }

    const momentum = {
      mom1w: momBack(5),
      mom1m: momBack(21),
      mom6m: momBack(127),
      mom12m: momBack(253),
      mom3y: momBack(756),
      mom5y: momBack(1260),
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
