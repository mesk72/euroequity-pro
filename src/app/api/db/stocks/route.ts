import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 0
export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

function jsonNoCache(body: any, init?: any) {
  const res = NextResponse.json(body, init)
  res.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0')
  res.headers.set('Pragma', 'no-cache')
  res.headers.set('Expires', '0')
  res.headers.set('CDN-Cache-Control', 'no-store')
  res.headers.set('Vercel-CDN-Cache-Control', 'no-store')
  return res
}

// FIX 3/8/2026 (sicurezza): questa route gira SUL SERVER e deve usare la
// chiave di servizio, non quella pubblica. La chiave pubblica e'
// estraibile dal browser: finche' le API la usavano, era necessario
// lasciare le tabelle leggibili a chiunque — cioe' l'intero database di
// prezzi e fondamentali era scaricabile da chiunque senza registrarsi.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// Rate limiting semplice per IP — protegge contro scraping massiccio
// dell'intero database. Non e' una difesa perfetta (la mappa vive solo
// nella singola istanza serverless), ma blocca gli script piu' semplici
// che farebbero centinaia di richieste rapide per scaricare tutto.
const RATE_LIMIT_WINDOW_MS = 60_000 // 1 minuto
const RATE_LIMIT_MAX = 40 // richieste massime per IP nella finestra
const rateLimitMap = new Map<string, { count: number; windowStart: number }>()

// Secondo livello: limite sul VOLUME totale di righe servite per IP
// nell'ultima ora — una singola chiamata puo' gia' restituire migliaia
// di righe (Global/ALL), quindi il solo conteggio delle richieste non
// basta a impedire di scaricare l'intero database in poche chiamate.
const ROWS_WINDOW_MS = 60 * 60_000 // 1 ora
const ROWS_MAX = 15_000 // righe totali massime servite per IP all'ora
const rowsServedMap = new Map<string, { rows: number; windowStart: number }>()

function isRowVolumeLimited(ip: string, rowsInThisResponse: number): boolean {
  const now = Date.now()
  const entry = rowsServedMap.get(ip)
  if (!entry || now - entry.windowStart > ROWS_WINDOW_MS) {
    rowsServedMap.set(ip, { rows: rowsInThisResponse, windowStart: now })
    return false
  }
  if (entry.rows > ROWS_MAX) return true
  entry.rows += rowsInThisResponse
  return false
}

function isRateLimited(ip: string): boolean {
  const now = Date.now()
  const entry = rateLimitMap.get(ip)
  if (!entry || now - entry.windowStart > RATE_LIMIT_WINDOW_MS) {
    rateLimitMap.set(ip, { count: 1, windowStart: now })
    return false
  }
  entry.count++
  if (entry.count > RATE_LIMIT_MAX) return true
  return false
}

// Pulizia periodica della mappa per non far crescere la memoria
// all'infinito nelle istanze a lunga durata.
setInterval(() => {
  const now = Date.now()
  rateLimitMap.forEach((entry, ip) => {
    if (now - entry.windowStart > RATE_LIMIT_WINDOW_MS * 5) rateLimitMap.delete(ip)
  })
}, RATE_LIMIT_WINDOW_MS * 5)

const ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

// Sottoinsieme visibile per chi NON e' il proprietario — i primi 500
// titoli al mondo per capitalizzazione di mercato. Ora letto da una
// tabella dedicata (top500_universe), calcolata una volta e stabile —
// NON piu' una cache in memoria per istanza, che su Vercel (piu'
// istanze serverless parallele) causava numeri diversi a seconda di
// quale istanza rispondeva, ciascuna con la propria cache locale.
// NON ricalcola nessun punteggio — decide solo QUALI righe includere
// nella risposta finale, i valori restano sempre quelli veri.
async function getTop500Keys(): Promise<Set<string>> {
  const { data, error } = await supabase.from('top500_universe').select('ticker,exchange')
  if (error || !data) return new Set()
  return new Set(data.map((s: any) => `${s.ticker}.${s.exchange}`))
}

const EMU_EXCHANGES = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR']
const FILTER_500M = new Set(['LSE','XETRA','PA','OM','SWX','MIL'])
const TOP_100_EX = new Set(['OB','MC','AS','BR','CPSE','HE','GR'])
const NO_FILTER = new Set(['VI','IR','LS'])
// APAC + North America: top N per market cap, solo titoli con company e sector
const APAC_TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, TSX: 400, ASX: 350, KRX: 400, SGX: 100, US: 2000 }

// Campi visibili SENZA login — identificazione base e prezzo, gia'
// pubblico altrove.
const PUBLIC_FIELDS = new Set([
  'ticker', 'exchange', 'isin', 'company', 'sector', 'country', 'flag',
  'website', 'description', 'primaryExchange', 'yahooTicker', 'inUniverse',
  'price', 'mktCap', 'lastPriceDate',
])

// Campi aggiuntivi visibili SOLO se loggato — punteggi finali e momentum.
// MAI i dati grezzi (PE, PB, EPS/Rev growth) ne' i rank esatti (0-100)
// dei singoli fattori — insieme al punteggio finale permetterebbero di
// ricostruire i pesi della formula per regressione statistica. Al posto
// del rank esatto, si mostra il QUINTILE (Top/2nd/Mid/4th/Bottom) — uno
// standard riconosciuto nell'analisi fattoriale (stile Fama-French), che
// da' informazione utile senza la precisione numerica necessaria per
// una regressione affidabile.
const SCORE_MOMENTUM_FIELDS = new Set([
  'valueScore', 'growthScore', 'combinedRank',
  'change1d', 'mom1w', 'mom1m', 'mom6m', 'mom12m',
  'revGrowthQuintile', 'epsGrowthQuintile', 'peTrailingQuintile', 'peForwardQuintile', 'pbQuintile',
  'sectorEpsGrowthQuintile', 'sectorRevGrowthQuintile',
  'continentEpsGrowthQuintile', 'continentRevGrowthQuintile',
  // Reverse Earnings Model — output del modello (Ke, crescita implicita),
  // non un dato grezzo in ingresso come PE/PB. Dimenticato quando e'
  // stato costruito il sistema di protezione, causa reale per cui la
  // sezione spariva dalla pagina titolo per chiunque non fosse
  // proprietario (23/7/2026).
  'ke', 'impliedGrowth10y',
  // Stessi campi del Reverse Earnings Model, dimenticati insieme a ke —
  // servono al calcolo interattivo del price target quando l'utente
  // modifica la crescita implicita nella pagina titolo.
  'epsNtmDcf', 'epsFwd24', 'epsFwd36', 'epsGrowth1224m', 'epsGrowth2436m', 'epsCagr2y',
])

function quintileFrom(rank: number | null | undefined): string | null {
  if (rank == null) return null
  if (rank >= 80) return 'Top Quintile'
  if (rank >= 60) return '2nd Quintile'
  if (rank >= 40) return 'Middle'
  if (rank >= 20) return '4th Quintile'
  return 'Bottom Quintile'
}

// Applica i quintili a TUTTI i fattori insieme, in un solo posto — evita
// di dimenticarne uno quando se ne aggiunge un altro.
function applyTiers(out: any, src: any) {
  out.revGrowthQuintile   = quintileFrom(src.rankRevGr)
  out.epsGrowthQuintile   = quintileFrom(src.rankEpsGr)
  out.peTrailingQuintile  = quintileFrom(src.rankPeLtm)
  out.peForwardQuintile   = quintileFrom(src.rankPeNtm)
  out.pbQuintile          = quintileFrom(src.rankPb)
}

function redactForGuest<T extends Record<string, any>>(obj: T): T {
  const out: any = {}
  for (const key of Object.keys(obj)) {
    out[key] = PUBLIC_FIELDS.has(key) ? obj[key] : null
  }
  applyTiers(out, obj)
  return out
}

function redactRawData<T extends Record<string, any>>(obj: T): T {
  const allowed = new Set(Array.from(PUBLIC_FIELDS).concat(Array.from(SCORE_MOMENTUM_FIELDS)))
  const out: any = {}
  for (const key of Object.keys(obj)) {
    out[key] = allowed.has(key) ? obj[key] : null
  }
  applyTiers(out, obj)
  return out
}

async function fetchLatestPrices(exchangeList: string[]) {
  // FIX 5/8/2026 — FONTE UNICA: legge da latest_prices_mv, una VISTA
  // MATERIALIZZATA calcolata su prices_eod (la stessa tabella che
  // alimenta il grafico). Prima leggeva la tabella latest_prices, che
  // veniva scritta separatamente dagli script: bastava che una delle due
  // scritture restasse indietro e lo stesso titolo mostrava due prezzi
  // diversi nella stessa pagina (caso riprodotto: ASML 1434,20 nello
  // screener contro 1419,60 nel grafico). Una vista calcolata non puo'
  // divergere dalla sua fonte.
  // Legge da latest_prices_mv — vista PRE-CALCOLATA, aggiornata dagli script,
  // aggiornata una volta al giorno. Nessun calcolo pesante in tempo
  // reale: sostituisce tutti i tentativi precedenti (query dirette,
  // RPC con window function/DISTINCT ON) che erano corretti ma troppo
  // lenti su tutto l'universo (causa reale dei 20 secondi di
  // caricamento, 25/7/2026 — diagnosi Kimi, stesso principio gia'
  // usato per top500_universe e sector_aggregates).
  // FIX 4/8/2026 — CAUSA REALE della discrepanza fra grafico e tabella,
  // segnalata molte volte e mai risolta finora. Questa query NON era
  // paginata: PostgREST restituisce al massimo 1000 righe, quindi su
  // 3.001 titoli USA solo 1.000 ricevevano il prezzo aggiornato e gli
  // altri 2.001 ricadevano su fundamentals.price o, peggio, su
  // stocks.price (verificato su ASML: 1.560,80 fermo al 23 giugno).
  // Il grafico invece legge sempre prices_eod e mostrava il dato giusto:
  // di qui la divergenza. Ora si pagina, come gia' fatto altrove.
  const result: Record<string, { price: number; date: string; change1d: number | null }> = {}
  const PAGE = 1000
  const richieste: any[] = []
  for (const exchange of exchangeList) {
    for (let page = 0; page < 5; page++) {   // fino a 5.000 titoli per mercato
      richieste.push(
        supabase.from('latest_prices_mv')
          .select('ticker,exchange,price,price_date,change1d')
          .eq('exchange', exchange)
          .order('ticker', { ascending: true })
          .range(page * PAGE, page * PAGE + PAGE - 1)
      )
    }
  }
  const risposte = await Promise.all(richieste)
  for (const { data, error } of risposte) {
    if (error || !data) continue
    for (const row of data) {
      const key = `${row.ticker}.${row.exchange}`
      result[key] = { price: row.price, date: row.price_date, change1d: row.change1d }
    }
  }
  return result
}

async function fetchAllByExchange(table: string, select: string, exchangeList: string[], universeOnly = false) {
  // FIX 30/7/2026: la parallelizzazione del 29/7 lanciava SEMPRE 4 pagine
  // per OGNI exchange "per sicurezza" — per Global (23 mercati) sono 92
  // richieste simultanee verso Supabase, anche se quasi tutti i mercati
  // hanno poche centinaia di titoli e stanno in UNA pagina sola (solo US
  // supera le 1000 righe). Sospetto reale per i 21s residui su Global
  // dopo aver tolto il calcolo quintili: 92 connessioni parallele possono
  // incontrare limiti di concorrenza lato Supabase. Ora si chiede prima
  // UNA pagina per ogni exchange (23 richieste, non 92), e SOLO per chi
  // torna una pagina piena (1000 righe, segno che ce n'e' altra) si
  // chiedono le pagine successive, solo per quello specifico exchange.
  const PAGE = 1000
  const MAX_PAGES_PER_EXCHANGE = 4
  const buildQuery = (exchange: string, page: number) => {
    let query = supabase.from(table).select(select).eq('exchange', exchange)
    if (universeOnly) query = query.eq('in_universe', true)
    return query.order('ticker', { ascending: true }).range(page * PAGE, page * PAGE + PAGE - 1).limit(PAGE)
  }

  const firstPageResults = await Promise.all(
    exchangeList.map(exchange => buildQuery(exchange, 0).then(r => ({ exchange, ...r })))
  )

  const all: any[] = []
  const needMore: string[] = []
  for (const { exchange, data, error } of firstPageResults as any[]) {
    if (error || !data) continue
    all.push(...data)
    if (data.length === PAGE) needMore.push(exchange)
  }

  if (needMore.length > 0) {
    const extraRequests: any[] = []
    for (const exchange of needMore) {
      for (let page = 1; page < MAX_PAGES_PER_EXCHANGE; page++) {
        extraRequests.push(buildQuery(exchange, page))
      }
    }
    const extraResults = await Promise.all(extraRequests)
    for (const { data, error } of extraResults as any[]) {
      if (error || !data) continue
      all.push(...data)
    }
  }
  return all
}

async function fetchAll(table: string, select: string, exchangeList: string[]) {
  // FIX 30/7/2026: stesso principio di fetchAllByExchange — prima UNA
  // pagina, poi le altre SOLO se la prima torna piena, invece di sparare
  // sempre 12 pagine (fino a 4 delle quali inutili per un Global con
  // ~7.889 righe di fundamentals, che ne servono 8).
  const PAGE = 1000
  const MAX_PAGES = 12
  const buildQuery = (page: number) =>
    supabase.from(table).select(select).in('exchange', exchangeList)
      .order('ticker', { ascending: true }).range(page * PAGE, page * PAGE + PAGE - 1).limit(PAGE)

  let all: any[] = []
  const { data: firstData, error: firstErr } = await buildQuery(0)
  if (!firstErr && firstData) all = all.concat(firstData)
  if (!firstData || firstData.length < PAGE) return all

  const remainingPages = Array.from({ length: MAX_PAGES - 1 }, (_, i) => buildQuery(i + 1))
  const results = await Promise.all(remainingPages)
  for (const { data, error } of results as any[]) {
    if (error || !data) continue
    all = all.concat(data)
  }
  return all
}

function applyUniverseFilter(fundData: any[], stocksData: any[]) {
  // Il filtro universo è già applicato a livello DB tramite in_universe=true
  // Questa funzione ora serve solo per mappare i dati
  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  return stocksData
    .filter(s => fundMap[`${s.ticker}.${s.exchange}`])
    .map(s => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
}

function applyAPACFilter(fundData: any[], stocksData: any[]) {
  const fundMap: Record<string, any> = {}
  for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f

  const stockMap: Record<string, any> = {}
  for (const s of stocksData) stockMap[`${s.ticker}.${s.exchange}`] = s

  const TOP_N: Record<string, number> = { TSE: 1000, SEHK: 500, ASX: 350, TSX: 400, KRX: 400, SGX: 100, US: 2000 }
  const EXCL_SECTORS = new Set(['71','72','73','74','75','76','77'])

  // Filtra fundData - NON esclude se non in stockMap
  const filtered = fundData.filter(f => {
    if (f.ticker === 'G6M' && f.exchange === 'ASX') return false
    const s = stockMap[`${f.ticker}.${f.exchange}`]
    const sector = s?.sector ?? null
    if (sector && EXCL_SECTORS.has(sector)) return false
    return true
  })

  // Per exchange prendi top N per mktCap
  const byExchange: Record<string, any[]> = {}
  for (const f of filtered) {
    if (!byExchange[f.exchange]) byExchange[f.exchange] = []
    byExchange[f.exchange].push(f)
  }

  const result: any[] = []
  for (const [ex, funds] of Object.entries(byExchange)) {
    const topN = TOP_N[ex] ?? 9999
    const sorted = funds
      .sort((a, b) => (b.mkt_cap ?? 0) - (a.mkt_cap ?? 0))
      .slice(0, topN)
    for (const f of sorted) {
      const s = stockMap[`${f.ticker}.${f.exchange}`] || { ticker: f.ticker, exchange: f.exchange }
      result.push(mapStock(s, f))
    }
  }
  return result
}


export async function GET(req: NextRequest) {
  // Rate limiting per IP — blocca scraping massiccio
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
    || req.headers.get('x-real-ip')
    || 'unknown'
  if (isRateLimited(ip)) {
    return jsonNoCache({ error: 'Too many requests. Please slow down.' }, { status: 429 })
  }

  // Verifica proprietario — estratta in funzione riusabile cosi' puo'
  // girare IN PARALLELO col recupero dati (diagnosi Kimi 25/7/2026,
  // problema 2: la verifica utente in sequenza PRIMA di tutto il resto
  // era una causa concreta della lentezza sulla pagina titolo).
  async function verifyUser(authHeader: string): Promise<{ isOwner: boolean; isInstitutionalViewer: boolean; isLoggedIn: boolean }> {
    let isOwner = false, isInstitutionalViewer = false, isLoggedIn = false
    if (authHeader.startsWith('Bearer ')) {
      try {
        const { data: { user } } = await supabase.auth.getUser(authHeader.slice(7))
        if (user?.email) isLoggedIn = true
        if (user?.email === 'andreameschini19@gmail.com') isOwner = true
        if (!isOwner && user?.email) {
          const { data: viewerRow } = await supabase
            .from('institutional_viewers').select('email').eq('email', user.email).maybeSingle()
          if (viewerRow) isInstitutionalViewer = true
        }
      } catch {}
    }
    return { isOwner, isInstitutionalViewer, isLoggedIn }
  }

  const authHeader = req.headers.get('authorization') || ''
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const exchanges = req.nextUrl.searchParams.get('exchanges') || ''
  const search = req.nextUrl.searchParams.get('search') || ''
  const ticker = req.nextUrl.searchParams.get('ticker') || ''
  const tickersParam = req.nextUrl.searchParams.get('tickers') || '' // "TICKER.EXCHANGE,TICKER2.EXCHANGE2,..." — usato da MyScreen per caricare l'intera watchlist in una sola chiamata
  const limit = parseInt(req.nextUrl.searchParams.get('limit') || '0')

  // Per il ramo singolo titolo e per il ramo batch (tickers), la verifica
  // utente viene fatta DENTRO il Promise.all con le query dati (vedi
  // sotto) — qui la saltiamo per non farla due volte. Per tutti gli altri
  // rami, la facciamo subito.
  let isOwner = false, isInstitutionalViewer = false, isLoggedIn = false
  if (!(ticker && exchange) && !tickersParam) {
    ;({ isOwner, isInstitutionalViewer, isLoggedIn } = await verifyUser(authHeader))
  }

  try {
    let exList: string[] = []
    if (search || ticker) {
      exList = ALL_RANKED
    } else if (exchange === 'EMU') {
      exList = EMU_EXCHANGES
    } else if (exchange && exchange !== 'EZ' && exchange !== 'ALL') {
      exList = [exchange]
    } else if (exchanges) {
      exList = exchanges.split(',')
    } else {
      exList = ALL_RANKED
    }

    if (ticker && exchange) {
      const [stockRes, fundRes, histRes, userVerify] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,website,price,last_price_date,primary_exchange,description,yahoo_ticker,in_universe').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        supabase.from('fundamentals').select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf').eq('ticker', ticker).eq('exchange', exchange).limit(1),
        // Storico per il grafico E per il prezzo/variazione reali — query
        // diretta su UN solo titolo, sempre veloce (millisecondi). Restaurata
        // dopo che rimuoverla aveva rotto qualcosa che PRIMA funzionava
        // correttamente (23/7/2026) — fundamentals.price/change1d non e'
        // affidabile per tutti gli 8000 titoli, resta indietro per alcuni.
        supabase.from('prices_eod').select('date,adj_close').eq('ticker', ticker).eq('exchange', exchange).order('date', { ascending: false }).limit(400),
        // Verifica utente IN PARALLELO con i dati (diagnosi Kimi, problema
        // 2) — prima era sequenziale PRIMA di tutto il resto, aggiungendo
        // tempo morto ad ogni apertura di pagina titolo.
        verifyUser(authHeader),
      ])
      isOwner = userVerify.isOwner
      isInstitutionalViewer = userVerify.isInstitutionalViewer
      isLoggedIn = userVerify.isLoggedIn
      const s: any = stockRes.data?.[0] || {}
      const f: any = fundRes.data?.[0] || {}
      if (!s.ticker) return jsonNoCache({ stocks: [] })
      const mapped = mapStock(s, f)
      const hist: any[] = histRes.data || []
      if (hist.length > 1) {
        const latest = hist[0]
        const prevDay = hist[1]
        if (latest.adj_close != null) {
          mapped.price = latest.adj_close
          mapped.lastPriceDate = latest.date
        }
        if (prevDay && prevDay.adj_close) {
          mapped.change1d = latest.adj_close / prevDay.adj_close - 1
        }
      }
      if (!isOwner && !isInstitutionalViewer) {
        const top500 = await getTop500Keys()
        if (!top500.has(`${mapped.ticker}.${mapped.exchange}`)) {
          return jsonNoCache({ stocks: [], restricted: true, ticker: mapped.ticker, company: mapped.company })
        }
      }
      let finalMapped: any = mapped
      if (isOwner) {
        // nessuna restrizione
      } else if (!isLoggedIn) {
        finalMapped = redactForGuest(mapped)
      } else {
        finalMapped = redactRawData(mapped)
      }
      return jsonNoCache({ stocks: [finalMapped], source: 'supabase' })
    }

    if (tickersParam) {
      // FIX 29/7/2026: MyScreen (watchlist) chiamava questo endpoint UNA
      // VOLTA PER OGNI titolo in watchlist (in parallelo tra loro, ma
      // comunque N round trip HTTP separati — e ognuno rifaceva la
      // verifica utente con supabase.auth.getUser(), una chiamata di rete
      // a Supabase Auth ripetuta N volte per lo STESSO identico token).
      // Con una watchlist di decine di titoli diventava lento. Ora un
      // solo round trip per l'intera watchlist, una sola verifica utente.
      const pairs = tickersParam.split(',').map(p => {
        const idx = p.lastIndexOf('.')
        return idx > 0 ? { ticker: p.slice(0, idx), exchange: p.slice(idx + 1) } : null
      }).filter((p): p is { ticker: string; exchange: string } => !!p)
      if (!pairs.length) return jsonNoCache({ stocks: [] })
      const tickerList = Array.from(new Set(pairs.map(p => p.ticker)))
      const exList2 = Array.from(new Set(pairs.map(p => p.exchange)))
      const pairKeys = new Set(pairs.map(p => `${p.ticker}.${p.exchange}`))

      const [stockRes, fundRes, userVerify] = await Promise.all([
        supabase.from('stocks').select('ticker,exchange,isin,company,sector,country,flag,website,price,last_price_date,primary_exchange,description,yahoo_ticker,in_universe').in('ticker', tickerList).in('exchange', exList2),
        supabase.from('fundamentals').select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf').in('ticker', tickerList).in('exchange', exList2),
        verifyUser(authHeader),
      ])
      isOwner = userVerify.isOwner
      isInstitutionalViewer = userVerify.isInstitutionalViewer
      isLoggedIn = userVerify.isLoggedIn

      // .in()/.in() e' un incrocio (non coppie esatte): scarta le righe
      // che non corrispondono a una coppia ticker+exchange realmente
      // richiesta (es. stesso ticker su un altro mercato).
      const stocksData = (stockRes.data || []).filter((s: any) => pairKeys.has(`${s.ticker}.${s.exchange}`))
      const fundDataAll = (fundRes.data || []).filter((f: any) => pairKeys.has(`${f.ticker}.${f.exchange}`))
      const fundMap: Record<string, any> = {}
      for (const f of fundDataAll) fundMap[`${f.ticker}.${f.exchange}`] = f

      let stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))

      // Prezzo reale da prices_eod via latest_prices — stessa fonte del ramo bulk.
      try {
        const freshPrices = await fetchLatestPrices(exList2)
        for (const s of stocks) {
          const key = `${s.ticker}.${s.exchange}`
          const fresh = freshPrices[key]
          if (fresh) {
            s.price = fresh.price
            s.change1d = fresh.change1d
            s.lastPriceDate = fresh.date
          }
        }
      } catch {}

      if (!isOwner && !isInstitutionalViewer) {
        const top500 = await getTop500Keys()
        stocks = stocks.filter((s: any) => top500.has(`${s.ticker}.${s.exchange}`))
      }
      if (isOwner) {
        // nessuna restrizione
      } else if (!isLoggedIn) {
        stocks = stocks.map((s: any) => redactForGuest(s))
      } else {
        stocks = stocks.map((s: any) => redactRawData(s))
      }
      return jsonNoCache({ stocks, source: 'supabase' })
    }

    if (search) {
      const { data } = await supabase
        .from('stocks')
        .select('ticker,exchange,isin,company,sector,country,flag,website,primary_exchange')
        .or(`ticker.ilike.%${search}%,company.ilike.%${search}%`)
        .limit(limit > 0 ? limit : 20)
      const stocksData = data || []
      if (!stocksData.length) return jsonNoCache({ stocks: [] })
      const tickers = stocksData.map((s: any) => s.ticker)
      const { data: fundData } = await supabase
        .from('fundamentals')
        .select('ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf')
        .in('ticker', tickers)
      const fundMap: Record<string, any> = {}
      for (const f of (fundData || [])) fundMap[`${f.ticker}.${f.exchange}`] = f
      let stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))

      // Stessa fonte del ramo bulk — prezzo reale, mai il campo statico.
      try {
        const searchExList = Array.from(new Set(stocks.map((s: any) => s.exchange)))
        const freshPrices = await fetchLatestPrices(searchExList)
        for (const s of stocks) {
          const key = `${s.ticker}.${s.exchange}`
          const fresh = freshPrices[key]
          if (fresh) {
            s.price = fresh.price
            s.change1d = fresh.change1d
            s.lastPriceDate = fresh.date
          }
        }
      } catch {}

      if (!isOwner && !isInstitutionalViewer) {
        const top500 = await getTop500Keys()
        stocks = stocks.filter((s: any) => top500.has(`${s.ticker}.${s.exchange}`))
      }
      if (isOwner) {
        // nessuna restrizione
      } else if (!isLoggedIn) {
        stocks = stocks.map((s: any) => redactForGuest(s))
      } else {
        stocks = stocks.map((s: any) => redactRawData(s))
      }
      return jsonNoCache({ stocks, source: 'supabase' })
    }

    const isUSOnly = exList.length === 1 && exList[0] === 'US'

    // Per APAC leggi stocks con limit=5000 per assicurarsi di prendere tutti i record
    const stocksSelect = 'ticker,exchange,isin,company,sector,country,flag,website,primary_exchange,yahoo_ticker'
    const fundSelect = 'ticker,exchange,price,change1d,mkt_cap,pe_trailing,pe_forward,pb,ev_ebitda,roe,beta,eps_growth,rev_growth,value_score,growth_score,combined_rank,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr,mom1w,mom1m,mom6m,mom12m,rank_mom6_adj,rank_mom12_adj,ke,implied_growth_10y,eps_fwd24,eps_fwd36,eps_growth_12_24m,eps_growth_24_36m,eps_cagr_2y,eps_ntm_dcf'

    const [stocksData, fundData, freshPricesResult] = await Promise.all([
      fetchAllByExchange('stocks', stocksSelect, exList, true),
      fetchAll('fundamentals', fundSelect, exList),
      // Non dipende da stocksData/fundData (usa solo exList, gia' noto) —
      // eseguito IN PARALLELO invece che dopo, per non sommare i tempi
      // (causa reale dei 20 secondi di caricamento, 23/7/2026). Stesso
      // identico calcolo di prima, solo avviato prima.
      fetchLatestPrices(exList).catch(() => ({} as Record<string, { price: number; date: string; change1d: number | null }>)),
    ])

    let stocks: any[]
    if (isUSOnly) {
      const fundMap: Record<string, any> = {}
      for (const f of fundData) fundMap[`${f.ticker}.${f.exchange}`] = f
      stocks = stocksData.map((s: any) => mapStock(s, fundMap[`${s.ticker}.${s.exchange}`] || {}))
    } else {
      // Unificato su applyUniverseFilter: si fida di in_universe=true, ora
      // affidabile su tutti i continenti grazie alla verifica Leeway
      // aggiunta alla costruzione dell'universo. applyAPACFilter (che
      // ricalcolava il top-N da zero ignorando in_universe, includendo
      // quindi anche titoli ormai esclusi rimasti nei fondamentali) non
      // serve piu' ed era la causa dello scarto tra "US" (corretto) e
      // "North America"/"Asia Pacific" combinati (gonfiati).
      stocks = applyUniverseFilter(fundData, stocksData)
    }

    // Prezzo/variazione reali da prices_eod, mai dal campo statico
    // fundamentals.price/change1d — non affidabile per tutti gli 8000
    // titoli (alcuni restano indietro, es. 9984.TSE mostrava 10.65%
    // invece del vero 6.03%, 23/7/2026). Gia' calcolato in parallelo sopra.
    {
      const freshPrices = freshPricesResult
      for (const s of stocks) {
        const key = `${s.ticker}.${s.exchange}`
        const fresh = freshPrices[key]
        if (fresh) {
          s.price = fresh.price
          s.change1d = fresh.change1d
          s.lastPriceDate = fresh.date
        }
      }
    }

    if (!isOwner && !isInstitutionalViewer) {
      const top500 = await getTop500Keys()
      stocks = stocks.filter((s: any) => top500.has(`${s.ticker}.${s.exchange}`))
    }


    // FIX 30/7/2026 (Kimi + Claude): il calcolo di settore/continente
    // girava QUI ad ogni richiesta scorrendo tutte le righe (fino a
    // ~7.889 per Global) — causa principale dei 25s su Global. Le somme
    // parziali per (exchange, settore) sono ora precalcolate una volta al
    // giorno dagli script daily_*.py (tabella sector_quintile_partials) e
    // sono SOMMABILI: per qualsiasi combinazione di mercati richiesta
    // basta sommare le poche righe pertinenti (decine, non migliaia).
    let usedPrecomputed = false
    {
      const toQ = (r: number | null) => r == null ? null :
        r >= 80 ? 'Top Quintile' : r >= 60 ? '2nd Quintile' : r >= 40 ? 'Middle' : r >= 20 ? '4th Quintile' : 'Bottom Quintile'

      try {
        const { data: partials, error: partialsErr } = await supabase
          .from('sector_quintile_partials')
          .select('exchange,sector,sum_eps_weighted,sum_eps_weight,sum_rev_weighted,sum_rev_weight')
          .in('exchange', exList)

        if (!partialsErr && partials && partials.length > 0) {
          const bySector: Record<string, { epsW: number; epsWt: number; revW: number; revWt: number }> = {}
          let contEpsW = 0, contEpsWt = 0, contRevW = 0, contRevWt = 0
          for (const p of partials) {
            const sec = p.sector || 'Unknown'
            if (!bySector[sec]) bySector[sec] = { epsW: 0, epsWt: 0, revW: 0, revWt: 0 }
            bySector[sec].epsW += p.sum_eps_weighted || 0
            bySector[sec].epsWt += p.sum_eps_weight || 0
            bySector[sec].revW += p.sum_rev_weighted || 0
            bySector[sec].revWt += p.sum_rev_weight || 0
            contEpsW += p.sum_eps_weighted || 0
            contEpsWt += p.sum_eps_weight || 0
            contRevW += p.sum_rev_weighted || 0
            contRevWt += p.sum_rev_weight || 0
          }
          const sectorQuintile: Record<string, { eps: string | null; rev: string | null }> = {}
          for (const [sec, v] of Object.entries(bySector)) {
            sectorQuintile[sec] = {
              eps: toQ(v.epsWt > 0 ? v.epsW / v.epsWt : null),
              rev: toQ(v.revWt > 0 ? v.revW / v.revWt : null),
            }
          }
          const continentEps = toQ(contEpsWt > 0 ? contEpsW / contEpsWt : null)
          const continentRev = toQ(contRevWt > 0 ? contRevW / contRevWt : null)
          for (const s of stocks) {
            const sec = s.sector || 'Unknown'
            s.sectorEpsGrowthQuintile = sectorQuintile[sec]?.eps ?? null
            s.sectorRevGrowthQuintile = sectorQuintile[sec]?.rev ?? null
            s.continentEpsGrowthQuintile = continentEps
            s.continentRevGrowthQuintile = continentRev
          }
          usedPrecomputed = true
        }
      } catch {
        // ignora, cade nel fallback sotto
      }

      if (!usedPrecomputed) {
        // FALLBACK (Kimi): tabella vuota/non ancora popolata/errore — stesso
        // calcolo di prima, in JS sui dati grezzi, cosi' i quintili non
        // spariscono mai. Loggato per accorgersi se scatta troppo spesso.
        console.warn('[ALLERTA] sector_quintile_partials vuota o non leggibile: uso il calcolo JS di riserva (piu lento). Verificare che gli script daily_*_yahoo.py la stiano popolando.')
        const bySector: Record<string, any[]> = {}
        for (const s of stocks) {
          const sec = s.sector || 'Unknown'
          if (!bySector[sec]) bySector[sec] = []
          bySector[sec].push(s)
        }
        const wavgOver = (list: any[], field: string) => {
          let num = 0, den = 0
          for (const s of list) {
            if (s[field] == null || s.mktCap == null) continue
            num += s[field] * s.mktCap
            den += s.mktCap
          }
          return den > 0 ? num / den : null
        }
        const sectorQuintile: Record<string, { eps: string | null; rev: string | null }> = {}
        for (const [sec, list] of Object.entries(bySector)) {
          sectorQuintile[sec] = { eps: toQ(wavgOver(list, 'rankEpsGr')), rev: toQ(wavgOver(list, 'rankRevGr')) }
        }
        const continentEps = toQ(wavgOver(stocks, 'rankEpsGr'))
        const continentRev = toQ(wavgOver(stocks, 'rankRevGr'))
        for (const s of stocks) {
          const sec = s.sector || 'Unknown'
          s.sectorEpsGrowthQuintile = sectorQuintile[sec]?.eps ?? null
          s.sectorRevGrowthQuintile = sectorQuintile[sec]?.rev ?? null
          s.continentEpsGrowthQuintile = continentEps
          s.continentRevGrowthQuintile = continentRev
        }
      }
    }

    if (isOwner) {
      // nessuna restrizione
    } else if (!isLoggedIn) {
      stocks = stocks.map((s: any) => redactForGuest(s))
    } else {
      stocks = stocks.map((s: any) => redactRawData(s))
    }

    if (isRowVolumeLimited(ip, stocks.length)) {
      return jsonNoCache({ error: 'Hourly data volume limit reached. Please try again later.' }, { status: 429 })
    }

    return jsonNoCache({ stocks, source: 'supabase' })

  } catch (e) {
    return jsonNoCache({ error: 'Database error' }, { status: 500 })
  }
}

function mapStock(s: any, f: any) {
  return {
    ticker: s.ticker ?? f.ticker,
    exchange: s.exchange ?? f.exchange,
    isin: s.isin ?? null,
    company: s.company ?? f.company ?? null,
    inUniverse: s.in_universe ?? null,
    sector: s.sector ?? f.sector ?? null,
    country: s.country ?? null,
    flag: s.flag ?? null,
    website: s.website ?? null,
    // FIX 4/8/2026: niente piu' ricaduta su f.price / s.price. Erano
    // copie separate del prezzo, aggiornate da percorsi diversi e spesso
    // vecchie di settimane (stocks.price di ASML era fermo al 23 giugno).
    // Il prezzo viene ESCLUSIVAMENTE da latest_prices, che deriva da
    // prices_eod — la stessa e unica fonte che alimenta il grafico.
    // Se manca, resta null: meglio nessun numero che uno sbagliato.
    price: null as number | null,
    change1d: null as number | null,
    ke: f.ke ?? null,
    impliedGrowth10y: f.implied_growth_10y ?? null,
    epsNtmDcf: f.eps_ntm_dcf ?? null,
    epsFwd24: f.eps_fwd24 ?? null,
    epsFwd36: f.eps_fwd36 ?? null,
    epsGrowth1224m: f.eps_growth_12_24m ?? null,
    epsGrowth2436m: f.eps_growth_24_36m ?? null,
    epsCagr2y: f.eps_cagr_2y ?? null,
    // come price e change1d: la data viene da latest_prices, non dalla
    // copia in stocks (che per ASML era ferma al 23 giugno).
    lastPriceDate: null as string | null,
    volume: null,
    mktCap: f.mkt_cap != null ? Math.round(f.mkt_cap / 1000 * 100) / 100 : null,
    peTrail: f.pe_trailing ?? null,
    peFwd: f.pe_forward ?? null,
    pb: f.pb ?? null,
    evEbitda: f.ev_ebitda ?? null,
    roe: f.roe ?? null,
    // divYield RIMOSSO 20/8/2026: valorizzato solo su 2257 righe di 12720
    // (18%), residuo di caricamenti vecchi. TIKR non fornisce il dato e
    // nessuno script lo aggiorna. Servire un dato parziale e fermo e'
    // peggio che non servirlo: l'utente non ha modo di sapere che e'
    // vecchio. Se un domani si trova una fonte affidabile, si riattiva.
    beta: f.beta ?? null,
    epsGrowth: f.eps_growth ?? null,
    revGrowth: f.rev_growth ?? null,
    epsMom30d: null,
    mom1w: f.mom1w ?? null,
    mom1m: f.mom1m ?? null,
    mom6m: f.mom6m ?? null,
    mom12m: f.mom12m ?? null,
    valueScore: f.value_score ?? null,
    growthScore: f.growth_score ?? null,
    combinedRank: f.combined_rank ?? null,
    rankPeLtm: f.rank_pe_ltm ?? null,
    rankPeNtm: f.rank_pe_ntm ?? null,
    rankPb: f.rank_pb ?? null,
    rankEpsGr: f.rank_eps_gr ?? null,
    rankRevGr: f.rank_rev_gr ?? null,
    rankMom6Adj: f.rank_mom6_adj ?? null,
    rankMom12Adj: f.rank_mom12_adj ?? null,
    primaryExchange: s.primary_exchange ?? null,
    yahooTicker: s.yahoo_ticker ?? null,
    description: s.description ?? null,
  }
}

