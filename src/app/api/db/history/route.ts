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
  const days = parseInt(req.nextUrl.searchParams.get('days') || '365')

  if (!ticker || !exchange) {
    return NextResponse.json({ error: 'Missing params' }, { status: 400 })
  }

  try {
    // Legge da price_history — unica fonte dati storici
    const fromDate = new Date(Date.now() - (days + 100) * 86400000)
      .toISOString().slice(0, 10)

    const { data, error } = await supabase
      .from('price_history')
      .select('date,close')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .gte('date', fromDate)
      .order('date', { ascending: true })

    if (error) return NextResponse.json({ error: error.message }, { status: 500 })

    const history = (data || []).map((d: any) => ({
      date: d.date,
      open: d.close,
      high: d.close,
      low: d.close,
      close: d.close,
      adjusted_close: d.close,
      volume: null,
    }))

    const closes = history.map((d: any) => d.close).filter(Boolean) as number[]
    const n = closes.length
    const last = closes[n - 1]

    // Momentum calcolati con gli stessi offset del daily_load
    // ret(lag) = prices[-1] / prices[-(lag+1)] - 1
    const getMom = (lag: number): number | null => {
      if (n <= lag) return null
      const p = closes[n - 1 - lag] // stesso di prices.iloc[-(lag+1)]
      return p && p > 0 ? (last / p - 1) * 100 : null
    }

    const momentum = {
      mom1w: getMom(5), // 5 giorni borsa
      mom1m: getMom(21), // 21 giorni borsa
      mom6m: getMom(131), // 131 giorni borsa
      mom12m: getMom(252), // 252 giorni borsa
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
