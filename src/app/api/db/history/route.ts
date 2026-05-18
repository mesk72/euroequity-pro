import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 3600  // cache 1h — storico non cambia durante il giorno

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET(req: NextRequest) {
  const ticker   = req.nextUrl.searchParams.get('ticker')   || ''
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const days     = parseInt(req.nextUrl.searchParams.get('days') || '365')

  if (!ticker || !exchange) {
    return NextResponse.json({ error: 'Missing params' }, { status: 400 })
  }

  try {
    const fromDate = new Date(Date.now() - (days + 50) * 86400000)
      .toISOString().slice(0, 10)

    const { data, error } = await supabase
      .from('prices_eod')
      .select('date,open,high,low,close,adj_close,volume')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .gte('date', fromDate)
      .order('date', { ascending: true })

    if (error) return NextResponse.json({ error: error.message }, { status: 500 })

    // Normalizza formato compatibile con il frontend (usa adjusted_close)
    const history = (data || []).map((d: any) => ({
      date:           d.date,
      open:           d.open,
      high:           d.high,
      low:            d.low,
      close:          d.close,
      adjusted_close: d.adj_close || d.close,
      volume:         d.volume,
    }))

    // Calcola momentum dai prezzi storici
    const closes = history.map((d: any) => d.adjusted_close).filter(Boolean)
    const n      = closes.length
    const last   = closes[n - 1]

    const mom = (offset: number) => {
      const idx = Math.max(0, n - offset)
      return closes[idx] ? (last / closes[idx] - 1) * 100 : null
    }

    const momentum = {
      mom1w:  mom(5),
      mom1m:  mom(21),
      mom6m:  mom(126),
      mom12m: mom(252),
    }

    return NextResponse.json({ history, momentum })
  } catch {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
