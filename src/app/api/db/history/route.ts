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

  // Stessa verifica reale usata in /api/db/stocks — senza un token
  // valido, niente storico prezzi ne' momentum.
  let verifiedUserId: string | null = null
  const authHeader = req.headers.get('authorization') || ''
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7)
    try {
      const { data: { user: verifiedUser } } = await supabase.auth.getUser(token)
      if (verifiedUser?.id) verifiedUserId = verifiedUser.id
    } catch {}
  }
  if (!verifiedUserId) {
    return NextResponse.json({
      history: [],
      momentum: { mom1w: null, mom1m: null, mom6m: null, mom12m: null, mom3y: null, mom5y: null }
    })
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
    // FIX 29/7/2026: usa lookback per DATA DI CALENDARIO, esattamente come
    // mom_new_weeks()/mom_new_months() negli script daily_*_yahoo.py — non
    // piu' un indice fisso di giorni di trading. Un indice fisso (es. 127gg
    // per 6 mesi) assume implicitamente che ogni finestra di calendario
    // contenga sempre lo stesso numero di sedute di borsa, il che e' falso
    // (festivita' variabili per mercato/anno: es. verificato 125 sedute
    // reali nella finestra a 6 mesi corrente, non 127) e produce uno scarto
    // sistematico crescente con la lunghezza della finestra rispetto al
    // valore mostrato nello screener/tabella. Con il lookback per data,
    // grafico e screener leggono la STESSA data di riferimento e quindi
    // restituiscono sempre lo stesso numero.
    const lastPrice = all[all.length - 1].adj_close as number
    const lastDate = new Date(all[all.length - 1].date + 'T00:00:00Z')

    // Replica dateutil.relativedelta: sottrae mesi clampando al ultimo
    // giorno valido del mese target (es. 31 gen - 1 mese = 31 dic; non overflow).
    const subtractMonths = (d: Date, months: number): Date => {
      const targetMonthIdx = d.getUTCMonth() - months
      const targetYear = d.getUTCFullYear() + Math.floor(targetMonthIdx / 12)
      const normMonth = ((targetMonthIdx % 12) + 12) % 12
      const lastDayOfTargetMonth = new Date(Date.UTC(targetYear, normMonth + 1, 0)).getUTCDate()
      const clampedDay = Math.min(d.getUTCDate(), lastDayOfTargetMonth)
      return new Date(Date.UTC(targetYear, normMonth, clampedDay))
    }

    const momByCalendar = (opts: { daysBack?: number; monthsBack?: number }): number | null => {
      const target = opts.monthsBack != null
        ? subtractMonths(lastDate, opts.monthsBack)
        : new Date(lastDate.getTime() - (opts.daysBack || 0) * 86400000)
      const targetPlus1Str = new Date(target.getTime() + 86400000).toISOString().slice(0, 10)
      // 'all' e' ordinato per data ascendente: il primo record >= target+1
      // e' esattamente il min(candidates) usato in Python.
      const ref = all.find((d: any) => d.date >= targetPlus1Str)
      if (!ref) return null
      const p = ref.adj_close
      return p && p > 0 ? (lastPrice / p - 1) * 100 : null
    }

    const momentum = {
      mom1w: momByCalendar({ daysBack: 7 }),
      mom1m: momByCalendar({ monthsBack: 1 }),
      mom6m: momByCalendar({ monthsBack: 6 }),
      mom12m: momByCalendar({ monthsBack: 12 }),
      mom3y: momByCalendar({ monthsBack: 36 }),
      mom5y: momByCalendar({ monthsBack: 60 }),
    }

    return NextResponse.json({ history, momentum })

  } catch (e) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}
