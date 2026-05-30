export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Questo endpoint viene chiamato da Vercel Cron ogni 5 minuti
// Configura in vercel.json:
// "crons": [{ "path": "/api/cron/update-live", "schedule": "*/5 8-18 * * 1-5" }]

const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'
const LEEWAY_KEY  = process.env.LEEWAY_KEY || ''

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!  // service_role per poter scrivere
)

const EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','AT']

async function fetchLiveQuotes(exchange: string) {
  const url = `${LEEWAY_BASE}/livequotes/${exchange}?apitoken=${LEEWAY_KEY}`
  const r = await fetch(url, { cache: 'no-store' })
  if (!r.ok) return []
  return r.json()
}

export async function GET(req: NextRequest) {
  // Verifica secret per sicurezza
  const auth = req.headers.get('authorization')
  if (auth !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let total = 0

  for (const exchange of EXCHANGES) {
    try {
      const quotes = await fetchLiveQuotes(exchange)
      if (!Array.isArray(quotes) || !quotes.length) continue

      const rows = quotes.map((q: any) => {
        const ticker    = q.ticker || q.code || q.symbol || ''
        const price     = parseFloat(q.close || q.price || q.last || '0') || null
        const prev      = parseFloat(q.previousClose || q.prev_close || '0') || null
        const change1d  = price && prev && prev !== 0
          ? ((price / prev) - 1) * 100
          : parseFloat(q.changePercent || q.change_p || '0') || null
        const changeAbs = price && prev ? price - prev : null

        return {
          ticker,
          exchange,
          price,
          change_1d:  change1d,
          change_abs: changeAbs,
          volume:     parseInt(q.volume || '0') || null,
          updated_at: new Date().toISOString(),
        }
      }).filter((r: any) => r.ticker && r.price)

      if (rows.length) {
        await supabase
          .from('prices_live')
          .upsert(rows, { onConflict: 'ticker,exchange' })
        total += rows.length
      }
    } catch (err) {
      console.error(`Error updating ${exchange}:`, err)
    }
  }

  return NextResponse.json({
    updated: total,
    timestamp: new Date().toISOString(),
  })
}
