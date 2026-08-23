import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

// FIX 9/8/2026 — CAUSA DELLA MANCATA INDICIZZAZIONE.
// La sitemap usava la chiave PUBBLICA. Il 3/8/2026 abbiamo chiuso
// l'accesso pubblico alle tabelle per sicurezza: da quel momento questa
// query restituisce ZERO righe e la sitemap pubblicava solo le 9 pagine
// fisse, senza nessuna delle ~7.900 schede titolo. Google non ha mai
// saputo che esistevano. La sitemap viene generata sul SERVER, quindi
// puo' e deve usare la chiave di servizio, come fanno le API del sito.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// Tutti i mercati coperti — EU (16), NA (2), APAC (5). GCC escluso finche'
// non e' live con copertura Leeway confermata.
const ALL_EXCHANGES = [
  // Europa
  'MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS',
  // Nord America
  'US','TSX',
  // Asia Pacifico
  'TSE','SEHK','ASX','KRX','SGX',
]

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // DOMINIO CANONICO: www.forwardalpha.pro
  // FIX 23/8/2026 — CAUSA DI 2.925 PAGINE NON INDICIZZATE.
  // Il sito e' servito da www.forwardalpha.pro; l'indirizzo senza www
  // risponde 308 e rimanda li'. La sitemap pero' dichiarava gli indirizzi
  // SENZA www: Google visitava ogni pagina indicata, veniva rimbalzato, e
  // la archiviava come "pagina con reindirizzamento" invece di
  // indicizzarla. Sitemap, canonical e robots.txt devono indicare il
  // dominio che serve davvero, non quello che rimanda.
  const baseUrl = 'https://www.forwardalpha.pro'

  // I ticker possono contenere spazi (NOVO B, COLO B) e punti (BRK.A,
  // IIP.UN): 190 indirizzi finivano nella sitemap con lo spazio grezzo,
  // che non e' un URL valido. Vanno codificati.
  const url = (ticker: string, exchange: string) =>
    `${baseUrl}/stock/${encodeURIComponent(ticker)}-${exchange}`

  // Pagine statiche
  const staticPages: MetadataRoute.Sitemap = [
    { url: baseUrl,                     lastModified: new Date(), changeFrequency: 'daily',   priority: 1.0 },
    { url: `${baseUrl}/news`,           lastModified: new Date(), changeFrequency: 'hourly',  priority: 0.9 },
    // RIMOSSI 9/8/2026: /screens e le sue tre sottopagine rispondono 404.
    // Next.js marca automaticamente le pagine inesistenti con noindex, ed
    // e' questa la segnalazione arrivata da Google Search Console
    // ("Esclusa in base al tag noindex"): stavamo indicando a Google
    // quattro indirizzi che non esistono.
    { url: `${baseUrl}/research`,       lastModified: new Date(), changeFrequency: 'weekly',  priority: 0.8 },
    { url: `${baseUrl}/about`,          lastModified: new Date(), changeFrequency: 'monthly', priority: 0.7 },
    { url: `${baseUrl}/legal`,          lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
  ]

  // Tutti i titoli in universe — tutte le borse
  let stocks: any[] = []
  let from = 0
  const PAGE = 1000
  while (true) {
    const { data, error } = await supabase
      .from('stocks')
      .select('ticker,exchange')
      .in('exchange', ALL_EXCHANGES)
      .eq('in_universe', true)
      .range(from, from + PAGE - 1)
    if (error || !data || data.length === 0) break
    stocks = stocks.concat(data)
    if (data.length < PAGE) break
    from += PAGE
  }

  // Top per market cap DAVVERO dal database, per regione separatamente (un
  //'top 60 globale' rischierebbe di sbilanciarsi tutto su una sola area).
  // Non piu' una lista scritta a mano che invecchia e puo' contenere ticker
  // sbagliati o non piu' esistenti — causa piu' probabile dei risultati
  // "senza senso" su Google.
  const REGION_EXCHANGES: Record<string, string[]> = {
    eu:   ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS'],
    na:   ['US','TSX'],
    apac: ['TSE','SEHK','ASX','KRX','SGX'],
  }

  let topByMktCap: any[] = []
  for (const exchanges of Object.values(REGION_EXCHANGES)) {
    const { data } = await supabase
      .from('fundamentals')
      .select('ticker,exchange,mkt_cap')
      .in('exchange', exchanges)
      .not('mkt_cap', 'is', null)
      .order('mkt_cap', { ascending: false })
      .limit(20)
    if (data) topByMktCap = topByMktCap.concat(data)
  }

  const topTickerKeys = new Set(
    topByMktCap.map((t: any) => `${t.ticker}-${t.exchange}`)
  )

  const TOP_TICKERS: MetadataRoute.Sitemap = topByMktCap.map((t: any) => ({
    url: url(t.ticker, t.exchange),
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 1.0,
  }))

  const stockPages: MetadataRoute.Sitemap = stocks
    .filter((s: any) => !topTickerKeys.has(`${s.ticker}-${s.exchange}`))
    .map((s: any) => ({
      url: url(s.ticker, s.exchange),
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.6,
    }))

  // Research slugs
  const { data: research } = await supabase
    .from('research_notes')
    .select('slug')
    .not('slug', 'is', null)
    .limit(200)

  const researchPages: MetadataRoute.Sitemap = (research || []).map((r: any) => ({
    url: `${baseUrl}/research/${r.slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.8,
  }))

  return [...staticPages, ...TOP_TICKERS, ...stockPages, ...researchPages]
}
