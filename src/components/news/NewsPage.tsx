'use client'

import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'

interface NewsItem {
  title: string
  link: string
  pubDate: string
  source: string
}

type Region = 'world' | 'americas' | 'europe' | 'asia'

const REGIONS: { key: Region; label: string; emoji: string }[] = [
  { key: 'world',    label: 'Global',        emoji: '🌐' },
  { key: 'americas', label: 'North America', emoji: '🌎' },
  { key: 'europe',   label: 'Europe',        emoji: '🌍' },
  { key: 'asia',     label: 'Asia Pacific',  emoji: '🌏' },
]

Write a structured report with these sections:
1. **Market Overview** (2-3 sentences summarizing the main market mood today)
2. **Key Themes** (3-4 bullet points of the most important themes/events moving markets)
3. **Sector Highlights** (which sectors are in focus and why)
4. **Key Risks & Opportunities** (what to watch)

Be factual, professional, and concise. Base your analysis ONLY on the provided headlines. Do not invent data.`

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 1000,
      messages: [{ role: 'user', content: prompt }]
    })
  })
  const d = await response.json()
  return d.content?.[0]?.text || 'Unable to generate report.'
}

const FEEDS: Record<Region, { name: string; url: string }[]> = {
  world: [
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
    { name: 'Motley Fool', url: 'https://www.fool.com/feeds/index.aspx' },
    { name: 'Google Finance', url: 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en' },
    { name: 'Google Markets Close', url: 'https://news.google.com/rss/search?q=markets+close+stocks+today+trading+session&hl=en&gl=US&ceid=US:en' },
  ],
  americas: [
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
    { name: 'CNBC Earnings', url: 'https://www.cnbc.com/id/15839069/device/rss/rss.html' },
    { name: 'Motley Fool', url: 'https://www.fool.com/feeds/index.aspx' },
    { name: 'Google US Close', url: 'https://news.google.com/rss/search?q=%22market+close%22+OR+%22stocks+end%22+OR+%22Wall+Street%22+S%26P500+nasdaq&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Fed', url: 'https://news.google.com/rss/search?q=Federal+Reserve+interest+rates+inflation+economy&hl=en&gl=US&ceid=US:en' },
  ],
  europe: [
    { name: 'Yahoo Finance EU', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Il Sole Mercati', url: 'https://www.ilsole24ore.com/rss/mercati.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/finanzen' },
    { name: 'Google EU Close', url: 'https://news.google.com/rss/search?q=european+stocks+close+DAX+FTSE+CAC+eurostoxx+today&hl=en&gl=US&ceid=US:en' },
    { name: 'Google ECB', url: 'https://news.google.com/rss/search?q=ECB+eurozone+inflation+rates+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Italy Borsa', url: 'https://news.google.com/rss/search?q=borsa+Milano+FTSE+MIB+azioni+chiusura&hl=it&gl=IT&ceid=IT:it' },
  ],
  asia: [
    { name: 'Yahoo Finance Asia', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'SCMP Markets', url: 'https://www.scmp.com/rss/92/feed' },
    { name: 'Japan Times Biz', url: 'https://www.japantimes.co.jp/feed/business/' },
    { name: 'Google Asia Close', url: 'https://news.google.com/rss/search?q=nikkei+close+hangseng+ASX+asia+markets+today&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Japan', url: 'https://news.google.com/rss/search?q=japan+nikkei+BOJ+yen+stocks+economy&hl=en&gl=JP&ceid=JP:en' },
    { name: 'Google China', url: 'https://news.google.com/rss/search?q=china+stocks+hang+seng+yuan+economy+CSI&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Australia', url: 'https://news.google.com/rss/search?q=ASX+australia+stocks+RBA+economy&hl=en&gl=AU&ceid=AU:en' },
  ],
}

function srcColor(s: string): string {
  if (s.includes('Reuters')) return '#ef4444'
  if (s.includes('CNBC')) return '#0ea5e9'
  if (s.includes('MarketWatch')) return '#2563eb'
  if (s.includes('Il Sole')) return '#ef4444'
  if (s.includes('Handelsblatt')) return '#f97316'
  if (s.includes('NHK')) return '#ec4899'
  if (s.includes('SCMP')) return '#10b981'
  if (s.includes('Financial')) return '#14b8a6'
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

export default function NewsPage() {
  const [data, setData] = useState<Record<Region, NewsItem[]>>({
    world: [], americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Region | 'report'>('world')
  const [lastUpdate, setLast] = useState('')
  const [countdown, setCountdown] = useState(900)
  const [report, setReport] = useState('')
  const [reportLoading, setReportLoading] = useState(false)
  const [reportDate, setReportDate] = useState('')

  const load = async () => {
    setLoading(true)
    const results: Record<Region, NewsItem[]> = { world: [], americas: [], europe: [], asia: [] }
    
    for (const region of ['world', 'americas', 'europe', 'asia'] as Region[]) {
      for (const { name, url } of FEEDS[region]) {
        try {
          const api = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(url)
          const r = await fetch(api)
          const d = await r.json()
          if (d.status === 'ok' && Array.isArray(d.items)) {
            const items: NewsItem[] = d.items
              .map((item: any) => ({
                title: (item.title || '').replace(/<[^>]+>/g, '').trim(),
                link: item.link || item.url || '#',
                pubDate: item.pubDate || item.published || new Date().toISOString(),
                source: name,
              }))
              .filter((n: NewsItem) => n.title.length > 3)
              .slice(0, 5)
            results[region].push(...items)
          }
        } catch (e: any) {
        }
      }
      // Deduplica e ordina
      const seen = new Set<string>()
      results[region] = results[region]
        .filter(n => { const k = n.title.slice(0, 50).toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true })
        .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
        .slice(0, 20)
    }
    
    setData(results)
    setLast(new Date().toLocaleTimeString())
    setCountdown(900)
    setLoading(false)
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 900000)
    return () => clearInterval(t)
  }, [])

  const handleGenerateReport = () => {
    const allNews = [
      ...data.world,
      ...data.americas,
      ...data.europe,
      ...data.asia,
    ].sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())

    if (allNews.length === 0) {
      setReport('No news available yet. Please wait for news to load and try again.')
      setReportDate(new Date().toLocaleString('en-US'))
      return
    }

    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    })

    // Raggruppa per regione
    const byRegion: Record<string, NewsItem[]> = {
      'Global': data.world.slice(0, 6),
      'North America': data.americas.slice(0, 6),
      'Europe': data.europe.slice(0, 6),
      'Asia Pacific': data.asia.slice(0, 6),
    }

    // Identifica temi chiave dalle fonti
    const allTitles = allNews.map(n => n.title.toLowerCase())
    const themes: string[] = []
    if (allTitles.some(t => t.includes('fed') || t.includes('federal reserve') || t.includes('interest rate')))
      themes.push('Central bank policy and interest rates remain in focus')
    if (allTitles.some(t => t.includes('inflation') || t.includes('cpi') || t.includes('price')))
      themes.push('Inflation data continues to drive market sentiment')
    if (allTitles.some(t => t.includes('earning') || t.includes('profit') || t.includes('revenue') || t.includes('result')))
      themes.push('Corporate earnings season influencing individual stock moves')
    if (allTitles.some(t => t.includes('oil') || t.includes('gold') || t.includes('commodit')))
      themes.push('Commodity markets showing notable price action')
    if (allTitles.some(t => t.includes('china') || t.includes('trade') || t.includes('tariff')))
      themes.push('Global trade dynamics and geopolitical tensions in view')
    if (allTitles.some(t => t.includes('tech') || t.includes('ai') || t.includes('nvidia') || t.includes('microsoft')))
      themes.push('Technology and AI sector driving market leadership')
    if (allTitles.some(t => t.includes('bank') || t.includes('financial') || t.includes('credit')))
      themes.push('Banking and financial sector news attracting attention')
    if (themes.length === 0)
      themes.push('Mixed signals across global markets', 'Investors monitoring macro developments')

    // Costruisci report
    let report = `**FORWARDALPHA DAILY MARKET BRIEFING**\n${today}\n\n`

    report += `**MARKET OVERVIEW**\n`
    const worldHeadlines = data.world.slice(0, 3).map(n => n.title).join(' | ')
    report += `Global financial markets are being shaped by the following developments: ${data.world[0]?.title || 'markets in focus'}. `
    report += `Sentiment across regions reflects a mix of macro and micro drivers as investors digest the latest news flow.\n\n`

    report += `**KEY THEMES**\n`
    themes.slice(0, 4).forEach(t => { report += `• ${t}\n` })
    report += '\n'

    report += `**REGIONAL SNAPSHOT**\n`
    Object.entries(byRegion).forEach(([region, items]) => {
      if (items.length === 0) return
      report += `\n${region}:\n`
      items.slice(0, 3).forEach(n => { report += `  • [${n.source}] ${n.title}\n` })
    })
    report += '\n'

    report += `**SOURCES**\n`
    const sources = [...new Set(allNews.map(n => n.source))].slice(0, 8)
    report += sources.join(' · ') + '\n\n'

    report += `_This briefing is compiled from ${allNews.length} headlines across ${sources.length} sources. ForwardAlpha ranks and scores are available for individual stocks mentioned._`

    setReport(report)
    setReportDate(new Date().toLocaleString('en-US'))
  }

  useEffect(() => {
    const t = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(t)
  }, [])

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const items = tab !== 'report' ? (data[tab as Region] || []) : []

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
            {data[key as Region]?.length > 0 && (
              <span style={{
                marginLeft: 5, fontSize: 10, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                background: tab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: tab === key ? '#000' : 'var(--orange)',
              }}>{data[key as Region].length}</span>
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
                  Generate an AI-powered daily market briefing based on today's headlines from Yahoo Finance, Reuters, CNBC and Seeking Alpha.
                </div>
                <button onClick={handleGenerateReport} disabled={loading}
                  style={{ padding: '10px 24px', borderRadius: 4, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', background: '#22c55e', color: '#000' }}>
                  📋 Generate Daily Report
                </button>
                <div style={{ fontSize: 10, color: 'var(--text4)', marginTop: 8 }}>
                  Powered by Claude AI · Based on real headlines only
                </div>
              </div>
            )}
            {reportLoading && (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <RefreshCw size={20} style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite', color: '#22c55e' }} />
                <p style={{ fontSize: 13, color: 'var(--text4)' }}>Analyzing today's headlines...</p>
              </div>
            )}
            {report && !reportLoading && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: 'var(--text4)' }}>Generated: {reportDate}</div>
                  <button onClick={handleGenerateReport}
                    style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer', border: '1px solid #22c55e', background: 'none', color: '#22c55e' }}>
                    🔄 Refresh
                  </button>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {report.split('**').map((part, i) =>
                    i % 2 === 1
                      ? <strong key={i} style={{ color: 'var(--orange)' }}>{part}</strong>
                      : <span key={i}>{part}</span>
                  )}
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
        ) : items.map((item, i) => (
          <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
            style={{
              display: 'block', padding: '12px 16px',
              background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
              borderLeft: '3px solid ' + srcColor(item.source),
              borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
              textDecoration: 'none',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.08)')}
            onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)')}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ flex: 1, fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>{item.title}</div>
              <div style={{ flexShrink: 0, textAlign: 'right', minWidth: 85 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: srcColor(item.source) }}>{item.source}</div>
                <div style={{ fontSize: 10, color: 'var(--text4)', marginTop: 2 }}>{timeAgo(item.pubDate)}</div>
              </div>
            </div>
          </a>
        ))
        }
      </div>
      <div style={{ fontSize: 10, color: 'var(--text4)', textAlign: 'center' }}>
        Reuters · CNBC · MarketWatch · Il Sole 24 Ore · Handelsblatt · NHK · SCMP · Auto-refresh 15 min
      </div>
    </div>
  )
}
