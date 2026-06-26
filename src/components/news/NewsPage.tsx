'use client'

import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import MarketStrip from './MarketStrip'

interface NewsItem {
  title: string
  link: string
  pubDate: string
  source: string
  ticker?: string
  exchange?: string
  company?: string
  valueScore?: number | null
  growthScore?: number | null
  bestScore?: number | null
  mktCap?: number | null
}

interface IndexData {
  name: string
  symbol: string
  price: number | null
  changePct: number | null
  time: string
}

const INDEX_LIST = [
  { name: 'S&P 500',       symbol: '^spx'  },
  { name: 'Nasdaq 100',    symbol: '^ndx'  },
  { name: 'Dow Jones',     symbol: '^dji'  },
  { name: 'DAX',           symbol: '^dax'  },
  { name: 'FTSE 100',      symbol: '^ukx'  },
  { name: 'CAC 40',        symbol: '^cac'  },
  { name: 'FTSE MIB',      symbol: 'mib.i' },
  { name: 'Euro Stoxx 50', symbol: '^sx5e' },
  { name: 'Nikkei 225',    symbol: '^nkx'  },
  { name: 'Hang Seng',     symbol: '^hsi'  },
  { name: 'ASX 200',       symbol: '^axjo' },
  { name: 'Gold',          symbol: 'gc.f'  },
  { name: 'Oil WTI',       symbol: 'cl.f'  },
  { name: 'EUR/USD',       symbol: 'eurusd'},
  { name: 'USD/JPY',       symbol: 'usdjpy'},
]

async function fetchIndices(): Promise<IndexData[]> {
  const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' })
  const results: IndexData[] = []
  await Promise.all(INDEX_LIST.map(async ({ name, symbol }) => {
    try {
      const stooqUrl = 'https://stooq.com/q/l/?s=' + symbol + '&f=sd2t2ohlcv&h&e=csv'
      const url = 'https://corsproxy.io/?' + encodeURIComponent(stooqUrl)
      const r = await fetch(url)
      if (!r.ok) { results.push({ name, symbol, price: null, changePct: null, time: now }); return }
      const text = await r.text()
      const lines = text.trim().split('\n')
      if (lines.length < 2) { results.push({ name, symbol, price: null, changePct: null, time: now }); return }
      const cols = lines[1].split(',')
      const close = parseFloat(cols[4])
      const open  = parseFloat(cols[3])
      const pct   = open > 0 ? ((close - open) / open) * 100 : null
      results.push({ name, symbol, price: isNaN(close) ? null : close, changePct: isNaN(pct as number) ? null : pct, time: now })
    } catch {
      results.push({ name, symbol, price: null, changePct: null, time: now })
    }
  }))
  return INDEX_LIST.map(({ name, symbol }) => results.find(r => r.symbol === symbol) || { name, symbol, price: null, changePct: null, time: now })
}

type Region = 'world' | 'americas' | 'europe' | 'asia'
type Tab = Region | 'report' | 'reportbest'

const REGIONS: { key: Region; label: string; emoji: string }[] = [
  { key: 'world',    label: 'Global',        emoji: '🌐' },
  { key: 'americas', label: 'North America', emoji: '🌎' },
  { key: 'europe',   label: 'Europe',        emoji: '🌍' },
  { key: 'asia',     label: 'Asia Pacific',  emoji: '🌏' },
]

const WORLD_RSS_FEEDS = [
  { name: 'Yahoo Finance',  url: 'https://finance.yahoo.com/rss/topstories' },
  { name: 'Yahoo Markets',  url: 'https://finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US' },
  { name: 'Seeking Alpha',  url: 'https://seekingalpha.com/market_currents.xml' },
  { name: 'Motley Fool',    url: 'https://www.fool.com/feeds/index.aspx' },
]

// Google News queries - fetchate via /api/yahoo-news proxy (server-side, no CORS)
const GOOGLE_NEWS_QUERIES = [
  { name: 'Google Wall St',   q: 'wall street stock market today close open' },
  { name: 'Google PreMkt',    q: 'premarket futures nasdaq sp500 dow jones morning' },
  { name: 'Google Mkt Close', q: 'stock market close today performance recap' },
  { name: 'Google Mkt Open',  q: 'stock market open today rally gains losses' },
  { name: 'Google Asia Mkt',  q: 'asia markets nikkei hang seng asx close today' },
  { name: 'Google Asia Cmmt', q: 'asia market commentary overnight session wrap' },
  { name: 'Google EU Mkt',    q: 'european markets DAX CAC FTSE open close today' },
  { name: 'Google EU Cmmt',   q: 'europe market commentary stocks bonds open' },
  { name: 'Google Fed',       q: 'fed ecb interest rate inflation central bank policy' },
  { name: 'Google Earnings',  q: 'earnings results revenue profit beat miss quarterly' },
  { name: 'Google Oil Gold',  q: 'oil gold commodity price today crude brent' },
  { name: 'Google Forex',     q: 'dollar euro yen pound forex currency market' },
  { name: 'Google Tech',      q: 'nvidia apple microsoft meta alphabet stock today' },
  { name: 'Google Banks',     q: 'jpmorgan goldman sachs bank financial stock' },
  { name: 'Google Morning',   q: 'morning brief stock market outlook today' },
  { name: 'Google Brief',     q: 'market wrap recap brief investing stocks' },
  { name: 'Futu Morning',     q: 'Futu morning brief market stock' },
  { name: 'GuruFocus',        q: 'site:gurufocus.com market close today' },
]

const EUROPE_EXTRA_FEEDS = [
  { name: 'FT Europe',      url: 'https://www.ft.com/europe?format=rss' },
  { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/mercati.xml' },
  { name: 'Handelsblatt',   url: 'https://www.handelsblatt.com/contentexport/feed/finanzen' },
  { name: 'Google EU Mkt',  url: 'https://news.google.com/rss/search?q=borsa+europea+mercati+azionari&hl=it&gl=IT&ceid=IT:it' },
  { name: 'Les Echos',      url: 'https://www.lesechos.fr/rss/rss_finance.xml' },
  { name: 'Google DAX',     url: 'https://news.google.com/rss/search?q=DAX+Frankfurt+Boerse+aktien&hl=de&gl=DE&ceid=DE:de' },
]

const ASIA_EXTRA_FEEDS = [
  { name: 'SCMP Markets',   url: 'https://www.scmp.com/rss/92/feed' },
  { name: 'Japan Times',    url: 'https://www.japantimes.co.jp/feed/business/' },
  { name: 'NHK Economy',    url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
  { name: 'Google Nikkei',  url: 'https://news.google.com/rss/search?q=nikkei+tokyo+stock+exchange&hl=en&gl=JP&ceid=JP:en' },
  { name: 'Google HK',      url: 'https://news.google.com/rss/search?q=hang+seng+hong+kong+market&hl=en&gl=HK&ceid=HK:en' },
  { name: 'Google ASX',     url: 'https://news.google.com/rss/search?q=ASX+australia+stock+market&hl=en&gl=AU&ceid=AU:en' },
]

function srcColor(s: string): string {
  if (s.includes('Reuters')) return '#ef4444'
  if (s.includes('CNBC')) return '#0ea5e9'
  if (s.includes('Yahoo')) return '#7c3aed'
  if (s.includes('Bloomberg')) return '#f59e0b'
  if (s.includes('Il Sole')) return '#ef4444'
  if (s.includes('Handelsblatt')) return '#f97316'
  if (s.includes('NHK')) return '#ec4899'
  if (s.includes('SCMP')) return '#10b981'
  if (s.includes('Seeking')) return '#f59e0b'
  if (s.includes('Motley')) return '#8b5cf6'
  if (s.includes('WSJ') || s.includes('Wall Street')) return '#1d4ed8'
  if (s.includes('FT') || s.includes('Financial Times')) return '#f97316'
  if (s.includes('Google')) return '#6b7280'
  return '#f97316'
}

function timeAgo(d: string): string {
  if (!d) return ''
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return m + 'm ago'
  const h = Math.floor(m / 60)
  if (h < 24) return h + 'h ago'
  return Math.floor(h / 24) + 'd ago'
}

async function fetchRSS(name: string, url: string): Promise<NewsItem[]> {
  try {
    const api = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(url)
    const r = await fetch(api)
    if (!r.ok) return []
    const d = await r.json()
    if (d.status !== 'ok' || !Array.isArray(d.items)) return []
    return d.items
      .map((item: any) => ({
        title: (item.title || '').replace(/<[^>]+>/g, '').trim(),
        link: item.link || '#',
        pubDate: item.pubDate || new Date().toISOString(),
        source: name,
      }))
      .filter((n: NewsItem) => n.title.length > 10)
      .slice(0, 20)
  } catch { return [] }
}

async function fetchTickerNews(
  region: string,
  tickers: { ticker: string; exchange: string; company: string; yahooTicker: string; valueScore?: number; growthScore?: number; bestScore?: number; mktCap?: number | null }[],
  onBatch: (news: NewsItem[]) => void
): Promise<void> {
  const seen: Record<string, boolean> = {}
  const maxAge = 18 * 60 * 60 * 1000 // 18 ore

  // Processa ticker in batch da 20 in parallelo
  // Usa Yahoo Finance RSS per singolo ticker - funziona con rss2json
  const batchSize = 50
  for (let i = 0; i < tickers.length; i += batchSize) {
    const batch = tickers.slice(i, i + batchSize)

    const batchResults = await Promise.all(
      batch.map(async (t) => {
        try {
          // Yahoo Finance RSS per yahooTicker specifico
          // Le notizie restituite sono GIA' specifiche per quel titolo
          const gr = await fetch('/api/yahoo-news?ticker=' + encodeURIComponent(t.yahooTicker || t.ticker) + '&company=' + encodeURIComponent(t.company || '') + '&exchange=' + encodeURIComponent(t.exchange || '') + '&yahooTicker=' + encodeURIComponent(t.yahooTicker || ''))
          if (!gr.ok) return []
          const gd = await gr.json()
          if (!Array.isArray(gd.items) || gd.items.length === 0) return []
          // Filtro rigoroso: tutte le parole significative del nome devono essere nel titolo
          const STOP = new Set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co','The','Holdings','International','Global','Company','Corporation','Limited','de','et','und','of','and'])
          const nameWords = t.company.split(' ')
            .map((w: string) => w.replace(/[^a-zA-Z0-9]/g, '').toLowerCase())
            .filter((w: string) => w.length >= 4 && !STOP.has(w.charAt(0).toUpperCase() + w.slice(1)))
          const wordsToMatch = nameWords.slice(0, 3)

          return gd.items
            .map((item: any) => ({
              title: (item.title || '').replace(/<[^>]+>/g, '').trim(),
              link: item.link || '#',
              pubDate: item.pubDate || new Date().toISOString(),
              source: item.source || 'Yahoo Finance',
              ticker: t.ticker,
              exchange: t.exchange,
              company: t.company,
              valueScore: t.valueScore,
              growthScore: t.growthScore,
              bestScore: t.bestScore,
              mktCap: t.mktCap ?? null,
            }))
            .filter((n: NewsItem) => {
              if (n.title.length < 10) return false
              if (Date.now() - new Date(n.pubDate).getTime() > maxAge) return false
              if ((n.source || '').toLowerCase().includes('tradingview')) return false
              if (wordsToMatch.length === 0) return false
              const titleLower = n.title.toLowerCase()
              const allMatch = wordsToMatch.every((w: string) => titleLower.includes(w))
              if (!allMatch) return false
              const k = n.title.slice(0, 60).toLowerCase()
              if (seen[k]) return false
              seen[k] = true
              return true
            })
            .slice(0, 3)
        } catch { return [] }
      })
    )

    const batchNews: NewsItem[] = batchResults.flat()
      .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())

    if (batchNews.length > 0) onBatch(batchNews)
  }
}

const EMPTY: Record<Region, NewsItem[]> = { world: [], americas: [], europe: [], asia: [] }

export default function NewsPage() {
  const [data, setData] = useState<Record<Region, NewsItem[]>>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('world')
  const [lastUpdate, setLast] = useState('')
  const [countdown, setCountdown] = useState(900)
  const [report, setReport] = useState('')
  const [reportDate, setReportDate] = useState('')
  const [reportLoading, setReportLoading] = useState(false)
  const [reportBest, setReportBest] = useState('')
  const [reportBestDate, setReportBestDate] = useState('')
  const [reportBestLoading, setReportBestLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [indices, setIndices] = useState<IndexData[]>([])

  const load = async () => {
    setLoading(true)
    // Reset dati
    setData({ world: [], americas: [], europe: [], asia: [] })

    // World + EU extra + Asia extra + Google News in parallelo
    const [worldRssResults, euResults, asiaResults, googleResults] = await Promise.all([
      Promise.all(WORLD_RSS_FEEDS.map(({ name, url }) => fetchRSS(name, url))),
      Promise.all(EUROPE_EXTRA_FEEDS.map(({ name, url }) => fetchRSS(name, url))),
      Promise.all(ASIA_EXTRA_FEEDS.map(({ name, url }) => fetchRSS(name, url))),
      // Google News via server proxy
      Promise.all(GOOGLE_NEWS_QUERIES.map(async ({ name, q }) => {
        try {
          const url = 'https://news.google.com/rss/search?q=' + encodeURIComponent(q) + '&hl=en&gl=US&ceid=US:en'
          const r = await fetch('/api/yahoo-news?ticker=&company=&googleUrl=' + encodeURIComponent(url))
          if (!r.ok) return [] as NewsItem[]
          const d = await r.json()
          return (d.items || []).map((i: any) => ({
            title: i.title || '',
            link: i.link || '#',
            pubDate: i.pubDate || new Date().toISOString(),
            source: name,
          })) as NewsItem[]
        } catch { return [] as NewsItem[] }
      }))
    ])
    const worldAll: NewsItem[] = [...worldRssResults.flat(), ...googleResults.flat()]
    const euExtra: NewsItem[] = euResults.flat()
    const asiaExtra: NewsItem[] = asiaResults.flat()
    const worldMaxAge = 48 * 60 * 60 * 1000 // 48 ore
    const worldSeen: Record<string, boolean> = {}
    const worldNews = worldAll
      .filter(n => {
        if (Date.now() - new Date(n.pubDate).getTime() > worldMaxAge) return false
        const k = n.title.toLowerCase()
        if (worldSeen[k]) return false
        worldSeen[k] = true
        return true
      })
      .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      .slice(0, 50)
    setData(prev => ({ ...prev, world: worldNews }))
    setLoading(false) // Mostra subito world, le regioni caricano in background

    // Regioni: carica ticker dal DB poi scarica news progressivamente
    const maxT: Record<string, number> = { americas: 1500, europe: 1500, asia: 1500 }
    await Promise.all((['americas', 'europe', 'asia'] as Region[]).map(async region => {
      try {
        const tr = await fetch('/api/ticker-news?region=' + region)
        if (!tr.ok) return
        const td = await tr.json()
            const tickers = (td.tickers || []).slice(0, maxT[region])
        if (tickers.length === 0) return
        // Aggiungi feed extra per europa e asia
        const extraItems = region === 'europe' ? euExtra : region === 'asia' ? asiaExtra : []
        if (extraItems.length > 0) {
          setData(prev => {
            const maxAge = 24 * 60 * 60 * 1000
            const filtered = extraItems.filter(n => Date.now() - new Date(n.pubDate).getTime() < maxAge)
            const merged = [...(prev[region] || []), ...filtered]
              .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
              
            return { ...prev, [region]: merged }
          })
        }
        await fetchTickerNews(region, tickers, (batch) => {
          setData(prev => {
            const merged = [...(prev[region] || []), ...batch]
              .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
              
            return { ...prev, [region]: merged }
          })
        })
      } catch {}
    }))

    setLast(new Date().toLocaleTimeString())
    setCountdown(900)
  }

  const generateReport = async () => {
    setReportLoading(true)

    // Carica indici freschi
    let idxData: IndexData[] = indices
    try {
      idxData = await fetchIndices()
      setIndices(idxData)
    } catch {}

    const allNews = [
      ...data.world, ...data.americas, ...data.europe, ...data.asia,
    ].sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())

    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    })
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

    const fmtIdx = (idx: IndexData) => {
      const p = idx.price != null ? idx.price.toLocaleString('en-US', { maximumFractionDigits: 2 }) : 'N/A'
      const c = idx.changePct != null ? (idx.changePct >= 0 ? '+' : '') + idx.changePct.toFixed(2) + '%' : 'N/A'
      return idx.name + ': ' + p + ' (' + c + ')'
    }

    const allTitles = allNews.map(n => n.title.toLowerCase())
    const themes: string[] = []
    if (allTitles.some(t => t.includes('fed') || t.includes('federal reserve') || t.includes('interest rate')))
      themes.push('Central bank policy in focus')
    if (allTitles.some(t => t.includes('inflation') || t.includes('cpi')))
      themes.push('Inflation dynamics influencing rate expectations')
    if (allTitles.some(t => t.includes('earning') || t.includes('profit') || t.includes('revenue')))
      themes.push('Corporate earnings season moving individual stocks')
    if (allTitles.some(t => t.includes('oil') || t.includes('gold') || t.includes('commodit')))
      themes.push('Commodity markets volatile')
    if (allTitles.some(t => t.includes('china') || t.includes('trade') || t.includes('tariff')))
      themes.push('Trade tensions weighing on global risk sentiment')
    if (allTitles.some(t => t.includes('tech') || t.includes('ai') || t.includes('nvidia')))
      themes.push('Technology and AI sector driving market leadership')
    if (themes.length === 0)
      themes.push('Markets digesting mixed macro signals')

    let txt = '**FORWARDALPHA DAILY MARKET BRIEFING**\n'
    txt += today + ' · ' + time + '\n\n'

    txt += '**LIVE MARKET DATA**\n'
    txt += 'For real-time indices, commodities and FX see the ticker bar at the top of this page (S&P 500, Nasdaq, DAX, FTSE 100, Nikkei, Hang Seng, Gold, Oil, EUR/USD).\n\n'

    txt += '**KEY THEMES**\n'
    themes.forEach(t => { txt += '• ' + t + '\n' })
    txt += '\n'

    const now24h = Date.now() - 24 * 60 * 60 * 1000
    const fmtNewsItem = (n: NewsItem) => {
      let line = '• '
      if (n.ticker) line += '[' + n.ticker + '] '
      line += n.title
      if (n.valueScore != null) {
        line += ' | ForwardAlpha: Val ' + n.valueScore + ' Grw ' + n.growthScore + ' Best ' + n.bestScore
      }
      if (n.link) line += '\n  📰 ' + n.link
      if (n.ticker && n.exchange) {
        line += '\n  📊 ' + n.ticker + ' → https://forwardalpha.pro/stock/' + n.ticker + '-' + n.exchange
      }
      return line
    }

    // Filtra 24h, ordina per mktcap (bestScore DESC = proxy mktcap), max 1 per ticker
    // Americas: top 100 mktcap, Europe: top 50, Asia: top 50
    // Market Cap Report: ordina per mktCap reale, non per score
    const filterMktCap = (items: NewsItem[], topN: number) => {
      // Prima raggruppa per ticker e prendi la notizia più recente per ciascuno
      const byTicker = new Map<string, NewsItem>()
      for (const n of items) {
        if (!n.ticker) continue
        if (new Date(n.pubDate).getTime() <= now24h) continue
        const key = n.ticker + '.' + n.exchange
        const existing = byTicker.get(key)
        if (!existing || new Date(n.pubDate) > new Date(existing.pubDate)) {
          byTicker.set(key, n)
        }
      }
      // Ordina per mktCap DESC (i ticker arrivano già in ordine mktCap dall'API)
      return Array.from(byTicker.values())
        .sort((a, b) => (b.mktCap || 0) - (a.mktCap || 0))
        .slice(0, topN)
    }

    const amNews = filterMktCap(data.americas, 10)
    const euNews = filterMktCap(data.europe,   10)
    const apNews = filterMktCap(data.asia,     10)

    if (amNews.length > 0) {
      txt += '**NORTH AMERICA — Top stories by market cap**\n'
      amNews.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (euNews.length > 0) {
      txt += '**EUROPE — Top stories by market cap**\n'
      euNews.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (apNews.length > 0) {
      txt += '**ASIA PACIFIC — Top stories by market cap**\n'
      apNews.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }

    const sourcesSet: Record<string, boolean> = {}
    allNews.forEach(n => { sourcesSet[n.source] = true })
    txt += '_Sources: ' + Object.keys(sourcesSet).slice(0, 8).join(' · ') + '_'

    setReport(txt)
    setReportDate(new Date().toLocaleString('en-US'))
    setReportLoading(false)
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 900000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const t = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(t)
  }, [])

  const downloadReport = (reportText: string) => {
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    const lines = reportText.split('\n')
    let body = ''
    for (const line of lines) {
      if (line.trim() === '') { body += '<br>'; continue }
      // Heading **TESTO**
      if (line.startsWith('**') && line.endsWith('**')) {
        body += '<h2>' + line.replace(/\*\*/g, '') + '</h2>'
        continue
      }
      // Link articolo 📰 https://...
      const aMatch = line.match(/^\s*📰\s*(https?:\/\/\S+)/)
      if (aMatch) {
        body += '<p class="link-row">📰 <a href="' + aMatch[1] + '" target="_blank">Read article</a></p>'
        continue
      }
      // Stock page 📊 TICKER → https://...
      const sMatch = line.match(/^\s*📊\s*([A-Z0-9\.]+)\s*→\s*(https?:\/\/\S+)/)
      if (sMatch) {
        body += '<p class="link-row">📊 <a href="' + sMatch[2] + '" target="_blank" class="stock-link">' + sMatch[1] + ' — Stock page</a></p>'
        continue
      }
      // Bullet •
      if (line.trim().startsWith('•')) {
        const txt = line.trim().slice(1).trim().replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        body += '<p class="bullet">• ' + txt + '</p>'
        continue
      }
      // Riga normale con **bold**
      const txt = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      body += '<p>' + txt + '</p>'
    }

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ForwardAlpha Daily Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #111; line-height: 1.7; }
  h1 { color: #f97316; font-size: 22px; margin-bottom: 4px; }
  h2 { color: #f97316; font-size: 16px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #f9731640; padding-bottom: 4px; }
  p { margin: 4px 0; font-size: 14px; }
  .bullet { margin-left: 12px; }
  .link-row { margin-left: 24px; font-size: 13px; }
  a { color: #2563eb; text-decoration: underline; }
  .stock-link { color: #f97316; font-weight: 700; }
  strong { color: #f97316; }
  .meta { color: #666; font-size: 12px; margin-bottom: 16px; }
  hr { border: none; border-top: 1px solid #eee; margin: 16px 0; }
  .footer { color: #999; font-size: 11px; margin-top: 24px; font-style: italic; }
</style>
</head>
<body>
<h1>ForwardAlpha Daily Market Briefing</h1>
<p class="meta">${today} · Generated at ${new Date().toLocaleTimeString()}</p>
<hr>
${body}
<p class="footer">Generated by <a href="https://forwardalpha.pro">ForwardAlpha</a> — Global Equity Research</p>
</body>
</html>`

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'ForwardAlpha_Report_' + new Date().toISOString().slice(0,10) + '.html'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Report Best Score — top titoli per bestScore con notizie ultime 24h
  const generateReportBest = async () => {
    setReportBestLoading(true)
    const now24h = Date.now() - 24 * 60 * 60 * 1000
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    const time  = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

    const fmtNewsItem = (n: NewsItem) => {
      let line = '• '
      if (n.ticker) line += '[' + n.ticker + '] '
      line += n.title
      if (n.valueScore != null) line += ' | Val ' + n.valueScore + ' Grw ' + n.growthScore + ' Best ' + n.bestScore
      if (n.link) line += '\n  📰 ' + n.link
      if (n.ticker && n.exchange) line += '\n  📊 https://forwardalpha.pro/stock/' + n.ticker + '-' + n.exchange
      return line
    }

    // Filtra 24h, ordina per bestScore DESC (null in fondo), max 1 per ticker
    const filterBest = (items: NewsItem[], topN: number) => {
      const seen = new Set<string>()
      return items
        .filter(n => n.ticker && new Date(n.pubDate).getTime() > now24h)
        .sort((a, b) => {
          const bs_a = b.bestScore ?? -1
          const bs_b = a.bestScore ?? -1
          return bs_a - bs_b
        })
        .filter(n => { if (seen.has(n.ticker!)) return false; seen.add(n.ticker!); return true })
        .slice(0, topN)
    }

    const amBest = filterBest(data.americas, 10)
    const euBest = filterBest(data.europe,   10)
    const apBest = filterBest(data.asia,     10)

    let txt = `FORWARDALPHA — BEST SCORE REPORT\n${today} · ${time}\n\n`
    txt += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    txt += 'Top stories by Best Score — last 24h\n'
    txt += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'

    if (amBest.length > 0) {
      txt += '**NORTH AMERICA — Best Score Leaders**\n'
      amBest.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (euBest.length > 0) {
      txt += '**EUROPE — Best Score Leaders**\n'
      euBest.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (apBest.length > 0) {
      txt += '**ASIA PACIFIC — Best Score Leaders**\n'
      apBest.forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }

    setReportBest(txt)
    setReportBestDate(today + ' · ' + time)
    setReportBestLoading(false)
  }

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const allItems: NewsItem[] = (tab !== 'report' && tab !== 'reportbest') ? (data[tab as Region] || []) : []
  const items: NewsItem[] = searchQuery.trim()
    ? allItems.filter(n => {
        const q = searchQuery.toLowerCase()
        return (n.ticker || '').toLowerCase().includes(q) ||
               (n.company || '').toLowerCase().includes(q) ||
               n.title.toLowerCase().includes(q)
      })
    : allItems

  return (
    <div className="space-y-4 p-3 fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {lastUpdate && <span style={{ fontSize: 10, color: 'var(--text4)' }}>{lastUpdate} · {fmt(countdown)}</span>}
          <button onClick={load} disabled={loading} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <RefreshCw size={14} style={{ color: loading ? 'var(--orange)' : 'var(--text4)', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </div>
      </div>

      <MarketStrip />

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{
              padding: '6px 14px', borderRadius: 4, fontSize: 13, fontWeight: 600,
              cursor: 'pointer', border: 'none',
              background: tab === key ? 'var(--orange)' : 'var(--surface)',
              color: tab === key ? '#000' : 'var(--text3)',
            }}>
            {emoji} {label}
            {data[key].length > 0 && (
              <span style={{
                marginLeft: 5, fontSize: 10, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                background: tab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: tab === key ? '#000' : 'var(--orange)',
              }}>{data[key].length}</span>
            )}
          </button>
        ))}
        <button onClick={() => setTab('report')}
          style={{
            padding: '6px 14px', borderRadius: 4, fontSize: 13, fontWeight: 600,
            cursor: 'pointer', border: 'none',
            background: tab === 'report' ? '#22c55e' : 'var(--surface)',
            color: tab === 'report' ? '#000' : 'var(--text3)',
          }}>
          📋 Market Cap Report
        </button>
        <button onClick={() => setTab('reportbest')}
          style={{
            padding: '6px 14px', borderRadius: 4, fontSize: 13, fontWeight: 600,
            cursor: 'pointer', border: 'none',
            background: tab === 'reportbest' ? 'var(--orange)' : 'var(--surface)',
            color: tab === 'reportbest' ? '#000' : 'var(--text3)',
          }}>
          ⭐ Best Score Report
        </button>
      </div>

      {tab !== 'report' && tab !== 'reportbest' && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="text"
            placeholder="🔍 Search by ticker or company... (e.g. MU, Nvidia)"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              flex: 1, padding: '6px 12px', borderRadius: 4, fontSize: 12,
              background: 'var(--surface)', border: '1px solid var(--border)',
              color: 'var(--text)', outline: 'none',
            }}
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')}
              style={{ padding: '4px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer', border: 'none', background: 'var(--surface)', color: 'var(--text4)' }}>
              ✕
            </button>
          )}
        </div>
      )}

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', minHeight: 200 }}>
        {tab === 'report' ? (
          <div style={{ padding: 20 }}>
            {!report && !reportLoading && (
              <div style={{ textAlign: 'center', padding: 32 }}>
                <div style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16 }}>
                  Generate a daily market briefing with live index data and today's headlines.
                </div>
                <button onClick={generateReport}
                  style={{ padding: '10px 24px', borderRadius: 4, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', background: '#22c55e', color: '#000' }}>
                  📋 Generate Daily Report
                </button>
              </div>
            )}
            {reportLoading && (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <RefreshCw size={20} style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite', color: '#22c55e' }} />
                <p style={{ fontSize: 13, color: 'var(--text4)' }}>Fetching live market data...</p>
              </div>
            )}
            {report && !reportLoading && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: 'var(--text4)' }}>Generated: {reportDate}</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={generateReport}
                      style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer', border: '1px solid #22c55e', background: 'none', color: '#22c55e' }}>
                      🔄 Refresh
                    </button>
                    <button onClick={() => downloadReport(report)}
                      style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer', border: '1px solid #3b82f6', background: 'none', color: '#3b82f6' }}>
                      📄 Download HTML
                    </button>
                  </div>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.9 }}>
                  {report.split('\n').map((line, li) => {
                    if (line.trim() === '') return <div key={li} style={{ height: 8 }} />
                    // Linea con link articolo (📰 https://...)
                    const articleMatch = line.match(/^\s*📰\s*(https?:\/\/\S+)/)
                    if (articleMatch) {
                      return <div key={li} style={{ marginLeft: 24, fontSize: 11 }}>
                        <span style={{ color: 'var(--text4)' }}>📰 </span>
                        <a href={articleMatch[1]} target="_blank" rel="noopener noreferrer"
                          style={{ color: '#60a5fa', textDecoration: 'underline', fontSize: 11 }}>Read article</a>
                      </div>
                    }
                    // Linea stock page (📊 TICKER → https://...)
                    const stockMatch = line.match(/^\s*📊\s*([A-Z0-9]+)\s*→\s*(https?:\/\/\S+)/)
                    if (stockMatch) {
                      return <div key={li} style={{ marginLeft: 24, fontSize: 11 }}>
                        <span style={{ color: 'var(--text4)' }}>📊 </span>
                        <a href={stockMatch[2]} target="_blank" rel="noopener noreferrer"
                          style={{ color: 'var(--orange)', textDecoration: 'underline', fontWeight: 700, fontSize: 11 }}>
                          {stockMatch[1]} — Stock page
                        </a>
                      </div>
                    }
                    // Linee normali con **bold**
                    const parts = line.split('**')
                    const rendered = parts.map((part, i) =>
                      i % 2 === 1
                        ? <strong key={i} style={{ color: 'var(--orange)' }}>{part}</strong>
                        : <span key={i}>{part}</span>
                    )
                    return <div key={li} style={{ marginBottom: 2 }}>{rendered}</div>
                  })}
                </div>
              </div>
            )}
          </div>
        ) : loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <RefreshCw size={20} style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite', color: 'var(--orange)' }} />
            <p style={{ fontSize: 13, color: 'var(--text4)' }}>Loading news...</p>
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <p style={{ fontSize: 13, color: 'var(--text4)', marginBottom: 12 }}>No news available.</p>
            <button onClick={load} style={{ color: 'var(--orange)', background: 'none', border: '1px solid var(--orange)', borderRadius: 4, padding: '6px 16px', cursor: 'pointer', fontSize: 12 }}>
              🔄 Retry
            </button>
          </div>
        ) : tab === 'reportbest' ? (
          <div style={{ padding: 20 }}>
            {!reportBest && !reportBestLoading && (
              <div style={{ textAlign: 'center', padding: 32 }}>
                <div style={{ fontSize: 14, color: 'var(--text3)', marginBottom: 16 }}>
                  Top stories ranked by ForwardAlpha Best Score — last 24h.
                </div>
                <button onClick={generateReportBest}
                  style={{ padding: '10px 24px', borderRadius: 4, fontSize: 13, fontWeight: 700,
                    cursor: 'pointer', border: 'none', background: 'var(--orange)', color: '#000' }}>
                  ⭐ Generate Best Score Report
                </button>
              </div>
            )}
            {reportBestLoading && (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <RefreshCw size={20} style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite', color: 'var(--orange)' }} />
                <p style={{ fontSize: 13, color: 'var(--text4)' }}>Building Best Score Report...</p>
              </div>
            )}
            {reportBest && !reportBestLoading && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: 'var(--text4)' }}>Generated: {reportBestDate}</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={generateReportBest}
                      style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                        border: '1px solid var(--orange)', background: 'none', color: 'var(--orange)' }}>
                      🔄 Refresh
                    </button>
                    <button onClick={() => downloadReport(reportBest)}
                      style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                        border: '1px solid #3b82f6', background: 'none', color: '#3b82f6' }}>
                      📄 Download HTML
                    </button>
                  </div>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.9 }}>
                  {reportBest.split('\n').map((line, li) => {
                    if (line.trim() === '') return <div key={li} style={{ height: 8 }} />
                    const articleMatch = line.match(/^\s*📰\s*(https?:\/\/\S+)/)
                    if (articleMatch) {
                      return <div key={li} style={{ marginLeft: 24, fontSize: 11 }}>
                        <span style={{ color: 'var(--text4)' }}>📰 </span>
                        <a href={articleMatch[1]} target="_blank" rel="noopener noreferrer"
                          style={{ color: '#60a5fa', textDecoration: 'underline', fontSize: 11 }}>Read article</a>
                      </div>
                    }
                    const stockMatch = line.match(/^\s*📊\s*(\S+)\s*→\s*(https?:\/\/\S+)/)
                    if (stockMatch) {
                      return <div key={li} style={{ marginLeft: 24, fontSize: 11, marginTop: 2 }}>
                        <a href={stockMatch[2]} target="_blank" rel="noopener noreferrer"
                          style={{ color: 'var(--orange)', textDecoration: 'none', fontWeight: 700, fontSize: 11 }}>
                          📊 {stockMatch[1]} →
                        </a>
                      </div>
                    }
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <div key={li} style={{ fontWeight: 700, color: 'var(--orange)',
                        fontSize: 12, marginTop: 16, marginBottom: 6,
                        borderBottom: '1px solid rgba(249,115,22,0.3)', paddingBottom: 4 }}>
                        {line.replace(/\*\*/g, '')}
                      </div>
                    }
                    if (line.startsWith('━')) {
                      return <div key={li} style={{ color: 'rgba(255,255,255,0.1)', fontSize: 10 }}>{line}</div>
                    }
                    return <div key={li} style={{ marginBottom: 4 }}>{line}</div>
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          items.map((item, i) => (
            <div key={i} style={{
              padding: '12px 16px',
              background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
              borderLeft: '3px solid ' + srcColor(item.source),
              borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
            }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <a href={item.link} target="_blank" rel="noopener noreferrer"
                    style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6, textDecoration: 'none', display: 'block' }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--orange)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--text)')}>
                    {item.title}
                  </a>
                  {item.ticker && item.valueScore != null && (
                    <div style={{ display: 'flex', gap: 6, marginTop: 4, alignItems: 'center' }}>
                      <span style={{ fontSize: 9, color: 'var(--text4)' }}>ForwardAlpha:</span>
                      <span style={{ fontSize: 9, fontWeight: 700, color: '#3b82f6' }}>Val {item.valueScore}</span>
                      <span style={{ fontSize: 9, fontWeight: 700, color: '#22c55e' }}>Grw {item.growthScore}</span>
                      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--orange)' }}>Best {item.bestScore}</span>
                    </div>
                  )}
                </div>
                <div style={{ flexShrink: 0, textAlign: 'right', minWidth: 90 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: srcColor(item.source) }}>{item.source}</div>
                  <div style={{ fontSize: 10, color: 'var(--text4)', marginTop: 2 }}>{timeAgo(item.pubDate)}</div>
                  {item.ticker && item.exchange && (
                    <a href={'/stock/' + item.ticker + '-' + item.exchange}
                      style={{ fontSize: 10, color: 'var(--orange)', fontWeight: 700, textDecoration: 'none', display: 'inline-block', marginTop: 3, padding: '1px 5px', border: '1px solid rgba(249,115,22,0.4)', borderRadius: 3 }}>
                      {item.ticker} ↗
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div style={{ fontSize: 10, color: 'var(--text4)', textAlign: 'center' }}>
        Yahoo Finance · Seeking Alpha · Google News · Il Sole 24 Ore · Handelsblatt · SCMP · NHK · Auto-refresh 15 min
      </div>
    </div>
  )
}
