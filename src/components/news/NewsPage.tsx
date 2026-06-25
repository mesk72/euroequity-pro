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
  valueScore?: number
  growthScore?: number
  bestScore?: number
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
type Tab = Region | 'report'

const REGIONS: { key: Region; label: string; emoji: string }[] = [
  { key: 'world',    label: 'Global',        emoji: '🌐' },
  { key: 'americas', label: 'North America', emoji: '🌎' },
  { key: 'europe',   label: 'Europe',        emoji: '🌍' },
  { key: 'asia',     label: 'Asia Pacific',  emoji: '🌏' },
]

const WORLD_FEEDS = [
  { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
  { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
  { name: 'Motley Fool',   url: 'https://www.fool.com/feeds/index.aspx' },
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
      .slice(0, 5)
  } catch { return [] }
}

async function fetchTickerNews(
  region: string,
  tickers: { ticker: string; exchange: string; company: string; yahooTicker: string; valueScore?: number; growthScore?: number; bestScore?: number }[],
  onBatch: (news: NewsItem[]) => void
): Promise<void> {
  const seen: Record<string, boolean> = {}
  const maxAge = 7 * 24 * 60 * 60 * 1000

  // Processa ticker in batch da 20 in parallelo
  // Usa Yahoo Finance RSS per singolo ticker - funziona con rss2json
  const batchSize = 20
  for (let i = 0; i < tickers.length; i += batchSize) {
    const batch = tickers.slice(i, i + batchSize)

    const batchResults = await Promise.all(
      batch.map(async (t) => {
        try {
          // Yahoo Finance RSS per yahooTicker specifico
          // Le notizie restituite sono GIA' specifiche per quel titolo
          const gr = await fetch('/api/yahoo-news?ticker=' + encodeURIComponent(t.yahooTicker || t.ticker))
          if (!gr.ok) return []
          const gd = await gr.json()
          if (!Array.isArray(gd.items) || gd.items.length === 0) return []
          // Filtro RIGOROSO: prima il ticker Yahoo, poi verifica nome azienda nel titolo
          const STOP = new Set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co','The','Holdings','International','Global','Company','Corporation','Limited','de','et','und','of','and'])
          // Prendi le parole significative del nome (minimo 4 caratteri, non stopword)
          const nameWords = t.company.split(' ')
            .map((w: string) => w.replace(/[^a-zA-Z0-9]/g, '').toLowerCase())
            .filter((w: string) => w.length >= 4 && !STOP.has(w.charAt(0).toUpperCase() + w.slice(1)))

          // La prima parola significativa del nome è il filtro principale
          const primaryWord = nameWords[0] || ''
          const secondWord = nameWords[1] || ''

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
            }))
            .filter((n: NewsItem) => {
              if (n.title.length < 10) return false
              if (Date.now() - new Date(n.pubDate).getTime() > maxAge) return false
              const titleLower = n.title.toLowerCase()
              // REGOLA: la prima parola significativa del nome DEVE essere nel titolo
              // E se esiste una seconda parola, anche quella deve esserci
              // Questo evita che "Wise" matchi "WSE" o "Innovation Partners" matchi "1801.HK"
              if (!primaryWord || primaryWord.length < 4) return false
              if (!titleLower.includes(primaryWord)) return false
              if (secondWord.length >= 4 && !titleLower.includes(secondWord)) {
                // Se la seconda parola non c'è, accetta solo se la prima è molto specifica (>6 chars)
                if (primaryWord.length <= 6) return false
              }
              const k = n.title.slice(0, 60).toLowerCase()
              if (seen[k]) return false
              seen[k] = true
              return true
            })
            .slice(0, 2)
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
  const [indices, setIndices] = useState<IndexData[]>([])

  const load = async () => {
    setLoading(true)
    // Reset dati
    setData({ world: [], americas: [], europe: [], asia: [] })

    // World: RSS feeds
    const worldAll: NewsItem[] = []
    for (const { name, url } of WORLD_FEEDS) {
      const items = await fetchRSS(name, url)
      worldAll.push(...items)
    }
    const worldSeen: Record<string, boolean> = {}
    const worldNews = worldAll
      .filter(n => { const k = n.title.slice(0, 50).toLowerCase(); if (worldSeen[k]) return false; worldSeen[k] = true; return true })
      .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      .slice(0, 25)
    setData(prev => ({ ...prev, world: worldNews }))
    setLoading(false) // Mostra subito world, le regioni caricano in background

    // Regioni: carica ticker dal DB poi scarica news progressivamente
    const maxT: Record<string, number> = { americas: 500, europe: 600, asia: 600 }
    await Promise.all((['americas', 'europe', 'asia'] as Region[]).map(async region => {
      try {
        const tr = await fetch('/api/ticker-news?region=' + region)
        if (!tr.ok) return
        const td = await tr.json()
            const tickers = (td.tickers || []).slice(0, maxT[region])
        if (tickers.length === 0) return
        await fetchTickerNews(region, tickers, (batch) => {
          setData(prev => {
            const merged = [...(prev[region] || []), ...batch]
              .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
              .slice(0, 50)
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

    const fmtNewsItem = (n: NewsItem) => {
      let line = '• '
      if (n.ticker) line += '[' + n.ticker + '] '
      line += n.title
      // Scores ForwardAlpha
      if (n.valueScore != null) {
        line += ' | ForwardAlpha: Val ' + n.valueScore + ' Grw ' + n.growthScore + ' Best ' + n.bestScore
      }
      // Link articolo
      if (n.link) line += '\n  📰 Article → ' + n.link
      // Link pagina ForwardAlpha
      if (n.ticker && n.exchange) {
        line += '\n  📊 ForwardAlpha → https://forwardalpha.pro/stock/' + n.ticker + '-' + n.exchange
      }
      return line
    }

    if (data.americas.length > 0) {
      txt += '**NORTH AMERICA**\n'
      data.americas.slice(0, 6).forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (data.europe.length > 0) {
      txt += '**EUROPE**\n'
      data.europe.slice(0, 6).forEach(n => { txt += fmtNewsItem(n) + '\n' })
      txt += '\n'
    }
    if (data.asia.length > 0) {
      txt += '**ASIA PACIFIC**\n'
      data.asia.slice(0, 6).forEach(n => { txt += fmtNewsItem(n) + '\n' })
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

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const items: NewsItem[] = tab !== 'report' ? (data[tab as Region] || []) : []

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
          📋 Daily Report
        </button>
      </div>

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
                  <button onClick={generateReport}
                    style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer', border: '1px solid #22c55e', background: 'none', color: '#22c55e' }}>
                    🔄 Refresh
                  </button>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.9 }}>
                  {report.split('\n').map((line, li) => {
                    // Evidenzia **testo** in arancione
                    const parts = line.split('**')
                    const rendered = parts.map((part, i) =>
                      i % 2 === 1
                        ? <strong key={i} style={{ color: 'var(--orange)' }}>{part}</strong>
                        : (() => {
                            // Trasforma → URL in link cliccabili
                            const urlMatch = part.match(/(.*?)→\s*(https?:\/\/\S+)(.*)/)
                            if (urlMatch) {
                              return <span key={i}>{urlMatch[1]}<a href={urlMatch[2]} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'underline', wordBreak: 'break-all' }}>Read article</a>{urlMatch[3]}</span>
                            }
                            return <span key={i}>{part}</span>
                          })()
                    )
                    return <div key={li} style={{ marginBottom: line === '' ? 8 : 2 }}>{rendered}</div>
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
