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
      open: d.close,
      high: d.close,
      low: d.close,
      close: d.close,
      adjusted_close: d.close,
      volume: null,
    }))

    // Calcola momentum con date di calendario — stessa logica del daily_load
    const dates = all.map((d: any) => d.date) as string[]
    const closes = all.map((d: any) => d.adj_close) as number[]
    const lastDate = new Date(dates[dates.length - 1])
    const lastPrice = closes[closes.length - 1]

    const getPrice = (targetDate: Date): number | null => {
      // Prende il prezzo del giorno di borsa precedente alla data target
      const target = targetDate.toISOString().slice(0, 10)
      for (let i = dates.length - 1; i >= 0; i--) {
        if (dates[i] <= target) return closes[i]
      }
      return null
    }

    const addMonths = (d: Date, months: number): Date => {
      const result = new Date(d)
      result.setMonth(result.getMonth() + months)
      return result
    }

    const addDays = (d: Date, days: number): Date => {
      const result = new Date(d)
      result.setDate(result.getDate() + days)
      return result
    }

    const p1w  = getPrice(addDays(lastDate, -7))
    const p1m  = getPrice(addMonths(lastDate, -1))
    const p6m  = getPrice(addMonths(lastDate, -6))
    const p12m = getPrice(addMonths(lastDate, -12))
    const p3y  = getPrice(addMonths(lastDate, -36))
    const p5y  = getPrice(addMonths(lastDate, -60))

    const mom = (p: number | null) => p && p > 0 ? (lastPrice / p - 1) * 100 : null

    const momentum = {
      mom1w:  mom(p1w),
      mom1m:  mom(p1m),
      mom6m:  mom(p6m),
      mom12m: mom(p12m),
      mom3y:  mom(p3y),
      mom5y:  mom(p5y),
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
