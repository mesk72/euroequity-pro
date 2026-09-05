import { Metadata } from 'next'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 3600

// Legge dal database con la chiave di servizio, non dall'API pubblica.
// Motivo: l'API nasconde i dati a chi non e' autenticato, e la generazione
// dei metadati avviene sul server senza sessione. Risultato precedente:
// descrizioni prive di P/E, P/B e capitalizzazione, cioe' proprio le
// parole con cui Google puo' posizionare la pagina.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

type Dati = {
  ticker: string
  exchange: string
  company: string | null
  sector: string | null
  country: string | null
  price: number | null
  mkt_cap: number | null
  pe_trailing: number | null
  in_universe: boolean | null
  ha_punteggi: boolean
  description: string | null
  website: string | null
  price_date: string | null
}

async function leggiTitolo(ticker: string, exchange: string): Promise<Dati | null> {
  try {
    const { data: s } = await supabase
      .from('stocks')
      .select('ticker,exchange,company,sector,country,in_universe,description,website')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .maybeSingle()
    if (!s) return null

    const { data: f } = await supabase
      .from('fundamentals')
      .select('mkt_cap,pe_trailing,value_score,growth_score')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .maybeSingle()

    const { data: p } = await supabase
      .from('latest_prices_mv')
      .select('price,price_date')
      .eq('ticker', ticker)
      .eq('exchange', exchange)
      .maybeSingle()

    return {
      ticker: s.ticker,
      exchange: s.exchange,
      company: s.company,
      sector: s.sector,
      country: s.country,
      price: p?.price ?? null,
      price_date: p?.price_date ?? null,
      description: s.description ?? null,
      website: s.website ?? null,
      mkt_cap: f?.mkt_cap ?? null,
      pe_trailing: f?.pe_trailing ?? null,
      in_universe: s.in_universe,
      // Si registra SOLO se i punteggi esistono, mai il loro valore.
      ha_punteggi: f?.value_score != null || f?.growth_score != null,
    }
  } catch {
    return null
  }
}

// ATTENZIONE ALLE UNITA' (verificate sul database il 9/8/2026):
// mkt_cap e' espressa in MILIONI di valuta locale (Apple = 4.562.774),
// div_yield e' gia' in PERCENTUALE (ASML = 0.53 significa 0,53%).
// Trattarle come unita' assolute produceva "Apple capitalizzazione 5
// milioni" e "ASML dividendo 53%": numeri palesemente sbagliati che
// Google avrebbe letto e mostrato nei risultati.
function capitalizzazione(milioni: number | null): string | null {
  if (milioni == null || milioni <= 0) return null
  if (milioni >= 1e6) return (milioni / 1e6).toFixed(2) + ' trilioni'
  if (milioni >= 1e3) return (milioni / 1e3).toFixed(1) + ' miliardi'
  return milioni.toFixed(0) + ' milioni'
}

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const [ticker, ...exParts] = params.id.split('-')
  const exchangeCode = exParts.join('-')
  const d = await leggiTitolo(ticker, exchangeCode)
  if (!d) return { title: `${ticker} | ForwardAlpha` }

  const nome = d.company || ticker
  const title = `${nome} (${d.ticker}) — analisi fondamentale e valutazione | ForwardAlpha`

  // SOLO dati di mercato pubblici: prezzo, capitalizzazione, multipli,
  // dividendo. Sono disponibili ovunque (Yahoo, Bloomberg): non c'e' nulla
  // di proprietario da proteggere e servono a farsi trovare.
  const pezzi: string[] = []
  pezzi.push(`${nome} (${d.ticker}, ${d.exchange})${d.sector ? ' — ' + d.sector : ''}${d.country ? ', ' + d.country : ''}.`)
  const mc = capitalizzazione(d.mkt_cap)
  if (mc) pezzi.push(`Capitalizzazione ${mc}.`)
  if (d.pe_trailing != null && Math.abs(d.pe_trailing) < 500) pezzi.push(`P/E storico ${d.pe_trailing.toFixed(1)}x.`)
  // P/B RIMOSSO 9/8/2026 su indicazione di Andrea: si pubblica il solo
  // P/E storico. Il rapporto prezzo/patrimonio e' uno degli ingressi del
  // Value Score, e per quanto sia un dato pubblico non c'e' motivo di
  // offrirlo gia' accostato agli altri su ottomila pagine.
  // Dividendo RIMOSSO 9/8/2026: il campo div_yield non compare in nessuna
  // metrica del sito e non viene aggiornato dagli script giornalieri.
  // Pubblicare un dato che non manteniamo e' peggio che non pubblicarlo:
  // Google lo mostrerebbe nei risultati e resterebbe fermo per sempre.

  // I punteggi proprietari vengono NOMINATI ma mai pubblicati: la pagina
  // si posiziona per ricerche tipo "<azienda> value score" senza che il
  // valore sia raccoglibile in massa da chi non e' registrato.
  if (d.ha_punteggi) {
    pezzi.push(`Value Score, Growth Score e Best Score proprietari ForwardAlpha, reverse earnings model e confronto di settore disponibili sulla scheda.`)
  } else {
    pezzi.push('Analisi quantitativa ForwardAlpha.')
  }

  const desc = 'ForwardAlpha — private research platform.'

  // NOINDEX SEMPRE — 5/9/2026.
  // Questo layout definisce metadati propri e SOVRASCRIVE quelli globali:
  // le 7.841 schede titolo restavano indicizzabili anche dopo aver messo
  // il noindex nel layout radice. Qui va ripetuto esplicitamente.
  const robots = { index: false, follow: false, nocache: true }

  return {
    title,
    description: desc,
    robots,
    alternates: { canonical: `https://www.forwardalpha.pro/stock/${params.id}` },
    openGraph: {
      title,
      description: desc,
      url: `https://www.forwardalpha.pro/stock/${params.id}`,
      siteName: 'ForwardAlpha',
      type: 'website',
    },
  }
}

export default async function StockLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { id: string }
}) {
  const [ticker, ...exParts] = params.id.split('-')
  const exchangeCode = exParts.join('-')
  const d = await leggiTitolo(ticker, exchangeCode)

  // Dati strutturati: dicono a Google in modo esplicito che la pagina
  // riguarda una societa' quotata, con il suo simbolo di borsa. Contengono
  // solo informazioni pubbliche - nessun punteggio proprietario.

  // CONTENUTO PER I MOTORI DI RICERCA RIMOSSO — 5/9/2026.
  // Esponeva prezzo, capitalizzazione, P/E, settore e paese in un blocco
  // leggibile da Google. Con il ritorno all'uso personale nessun dato deve
  // essere visibile a chi non e' autorizzato: il blocco e' stato tolto
  // insieme ai dati strutturati.

  return (
    <>
      {children}
    </>
  )
}
