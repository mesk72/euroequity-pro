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

  // Coppie ticker+mercato richieste, per il filtro esatto piu' sotto.
  // FIX 1/8/2026: si separa sull'ULTIMO punto, non sul primo — diversi
  // ticker contengono un punto (es. "ACO.X", "GO.U", "IIP.UN" in Canada),
  // e spezzando sul primo si otteneva "ACO" invece di "ACO.X".
  let wantedPairs: Set<string> | null = null
  if (tickersParam) {
    const pairs = tickersParam.split(',').map(p => p.trim()).filter(Boolean)
    wantedPairs = new Set<string>()
    const tickerList: string[] = []
    for (const p of pairs) {
      const i = p.lastIndexOf('.')
      if (i <= 0) continue
      const tk = p.slice(0, i)
      const ex = p.slice(i + 1)
      tickerList.push(tk)
      wantedPairs.add(tk + '.' + ex)
    }
    if (tickerList.length === 0) return NextResponse.json({ items: [] })
    query = query.in('ticker', Array.from(new Set(tickerList)))
  } else {
    query = query.eq('region', region)
  }

  const { data, error } = await query

  if (error) return NextResponse.json({ items: [] })

  // FIX 1/8/2026: il filtro sopra puo' restare solo sul ticker (PostgREST
  // non fa un IN su coppie di colonne), quindi qui si scartano le righe di
  // societa' OMONIME su altri mercati. Senza questo passaggio un wallet con
  // Roche (ROP.SWX) riceveva anche le notizie di Roper Technologies
  // (ROP.US); Sanofi (SAN.PA) quelle di Banco Santander (SAN.MC);
  // Bristol-Myers (BMY.US) quelle di Bloomsbury Publishing (BMY.LSE);
  // UCB (UCB.BR) quelle di United Community Banks (UCB.US). Le notizie
  // arrivavano quindi doppie e per meta' sbagliate.
  let items = data || []
  if (wantedPairs) {
    items = items.filter((n: any) => wantedPairs!.has(`${n.ticker}.${n.exchange}`))
  }

  const response = NextResponse.json({ items })
  response.headers.set('Cache-Control', 'public, s-maxage=1800, stale-while-revalidate=3600')
  return response
}
