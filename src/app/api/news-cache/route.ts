import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export const revalidate = 1800 // 30 min cache Vercel Edge

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'
  const limit  = parseInt(searchParams.get('limit') || '500')
  // Filtro opzionale per una lista specifica di ticker (es. "AAPL.US,MSFT.US")
  // — usato per mostrare solo le notizie dei titoli in un wallet, invece
  // di tutta la regione.
  const tickersParam = searchParams.get('tickers') || ''

  let query = supabase
    .from('news_cache')
    .select('*')
    .gte('fetched_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
    .order('best_score', { ascending: false, nullsFirst: false })
    .limit(limit)

  if (tickersParam) {
    const pairs = tickersParam.split(',').map(p => p.trim()).filter(Boolean)
    const tickerList = pairs.map(p => p.split('.')[0])
    query = query.in('ticker', tickerList)
  } else {
    query = query.eq('region', region)
  }

  const { data, error } = await query

  if (error) return NextResponse.json({ items: [] })

  const response = NextResponse.json({ items: data || [] })
  response.headers.set('Cache-Control', 'public, s-maxage=1800, stale-while-revalidate=3600')
  return response
}
