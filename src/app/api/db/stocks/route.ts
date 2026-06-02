export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Chiamato da Vercel Cron ogni giorno alle 18:30 IT (lun-ven)
// vercel.json: { "path": "/api/cron/update-live", "schedule": "30 16 * * 1-5" }

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

const EXCHANGE_SUFFIX: Record<string, string> = {
  'MIL':'.MI','XETRA':'.DE','PA':'.PA','LSE':'.L',
  'AS':'.AS','SWX':'.SW','OM':'.ST','OB':'.OL',
  'BR':'.BR','HE':'.HE','MC':'.MC','CPSE':'.CO',
  'AT':'.AT','VI':'.VI','LS':'.LS','IR':'.IR',
}

async function fetchYahooQuote(yahooTicker: string): Promise<{price: number, change1d: number} | null> {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yahooTicker)}?interval=1d&range=2d`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      cache: 'no-store'
    })
    if (!r.ok) return null
    const data = await r.json()
    const meta = data?.chart?.result?.[0]?.meta
    if (!meta?.regularMarketPrice) return null
    const price = meta.regularMarketPrice
    const prev = meta.chartPreviousClose || meta.previousClose
    const change1d = prev && prev !== 0 ? (price / prev - 1) : null
    return { price, change1d }
  } catch {
    return null
  }
}

export async function GET(req: NextRequest) {
  const auth = req.headers.get('authorization')
  if (process.env.CRON_SECRET && auth !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Legge tutti i ticker dal DB
  const { data: stocks } = await supabaseAdmin
    .from('stocks')
    .select('ticker,exchange')
    .in('exchange', Object.keys(EXCHANGE_SUFFIX))

  if (!stocks?.length) return NextResponse.json({ error: 'No stocks' })

  let ok = 0
  let errors = 0
  const rows: any[] = []

  for (const s of stocks) {
    const suffix = EXCHANGE_SUFFIX[s.exchange] || ''
    let yticker = s.ticker + suffix

    // Fix ticker nordici
    if (['.ST','.CO','.OL','.HE'].includes(suffix) && yticker.includes(' '))
      yticker = yticker.replace(' ', '-')
    if (suffix === '.L' && s.ticker.endsWith('.'))
      yticker = s.ticker.slice(0,-1) + suffix

    const q = await fetchYahooQuote(yticker)
    if (!q) { errors++; continue }

    rows.push({
      ticker: s.ticker,
      exchange: s.exchange,
      price: q.price,
      change_1d: q.change1d,
      updated_at: new Date().toISOString(),
    })
    ok++

    // Batch upsert ogni 100
    if (rows.length >= 100) {
      await supabaseAdmin.from('prices_live').upsert(rows.splice(0,100), { onConflict: 'ticker,exchange' })
    }
  }

  // Upload rimanenti
  if (rows.length > 0) {
    await supabaseAdmin.from('prices_live').upsert(rows, { onConflict: 'ticker,exchange' })
  }

  return NextResponse.json({ ok, errors, timestamp: new Date().toISOString() })
}
