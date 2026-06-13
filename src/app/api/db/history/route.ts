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
    const dates = all.map((d: any) => d.date) as string[]
    const closes = all.map((d: any) => d.adj_close) as number[]
    const lastDate = new Date(dates[dates.length - 1])
    const lastPrice = closes[closes.length - 1]

    const getClosestPrice = (targetDate: Date): number | null => {
      const target = targetDate.getTime()
      let closest = null
      let minDiff = Infinity
      for (let i = 0; i < dates.length; i++) {
        const diff = Math.abs(new Date(dates[i]).getTime() - target)
        if (diff < minDiff) { minDiff = diff; closest = closes[i] }
      }
      return closest
    }

    const daysBack = (days: number): Date => {
      const d = new Date(lastDate)
      d.setDate(d.getDate() - days)
      return d
    }

    const mom = (p: number | null) => p && p > 0 ? (lastPrice / p - 1) * 100 : null

    const momentum = {
      mom1w: mom(getClosestPrice(daysBack(7))),
      mom1m: mom(getClosestPrice(daysBack(31))),
      mom6m: mom(getClosestPrice(daysBack(182))),
      mom12m: mom(getClosestPrice(daysBack(365))),
      mom3y: mom(getClosestPrice(daysBack(1095))),
      mom5y: mom(getClosestPrice(daysBack(1826))),
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
