import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const FMP_BASE = 'https://financialmodelingprep.com/api/v3'
const FMP_KEY  = process.env.FMP_KEY || ''

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

const EXCHANGE_SUFFIX: Record<string, string> = {
  MIL: '.MI', XETRA: '.DE', PA: '.PA', AS: '.AS',
  MC:  '.MC', BR:    '.BR', LS: '.LS', VI: '.VI',
  HE:  '.HE', IR:    '.IR', AT: '.AT',
}

async function fmpQuote(symbols: string) {
  const url = `${FMP_BASE}/quote/${symbols}?apikey=${FMP_KEY}`
  const r = await fetch(url, { cache: 'no-store' })
  if (!r.ok) return []
  return r.json()
}

export async function GET(req: NextRequest) {
  const auth = req.headers.get('authorization')
  if (auth !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let total = 0
  const { data: stocks } = await supabase.from('stocks').select('ticker,exchange')
  if (!stocks?.length) return NextResponse.json({ error: 'No stocks' }, { status: 404 })

  const byExchange: Record<string, string[]> = {}
  for (const s of stocks) {
    if (!byExchange[s.exchange]) byExchange[s.exchange] = []
    byExchange[s.exchange].push(s.ticker)
  }

  for (const [exchange, tickers] of Object.entries(byExchange)) {
    const suffix  = EXCHANGE_SUFFIX[exchange] || ''
    const symbols = tickers.map(t => `${t}${suffix}`).join(',')
    try {
      const quotes = await fmpQuote(symbols)
      if (!Array.isArray(quotes) || !quotes.length) continue
      const rows = quotes.map((q: any) => {
        const sym    = q.symbol || ''
        const ticker = suffix ? sym.replace(suffix, '') : sym
        return { ticker, exchange, price: q.price || null,
          change_1d: q.changesPercentage || null,
          change_abs: q.change || null, volume: q.volume || null,
          updated_at: new Date().toISOString() }
      }).filter((r: any) => r.ticker && r.price)
      if (rows.length) {
        await supabase.from('prices_live').upsert(rows, { onConflict: 'ticker,exchange' })
        total += rows.length
      }
    } catch (err) { console.error(`Error ${exchange}:`, err) }
  }

  return NextResponse.json({ updated: total, timestamp: new Date().toISOString(), source: 'fmp' })
}
