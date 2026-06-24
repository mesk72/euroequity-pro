'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, Clock, ExternalLink } from 'lucide-react'

interface NewsItem {
  title: string
  link: string
  pubDate: string
  source: string
}

type Region = 'world' | 'americas' | 'europe' | 'asia'

// Feed caricati lato client tramite rss2json (chiamata dal browser, niente CORS)
const FEEDS: Record<Region, { name: string; url: string }[]> = {
  world: [
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
    { name: 'Google Markets', url: 'https://news.google.com/rss/search?q=global+markets+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Commodities', url: 'https://news.google.com/rss/search?q=oil+gold+commodities&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Central Banks', url: 'https://news.google.com/rss/search?q=central+bank+interest+rates&hl=en&gl=US&ceid=US:en' },
  ],
  americas: [
    { name: 'CNBC US', url: 'https://www.cnbc.com/id/10000664/device/rss/rss.html' },
    { name: 'CNBC Markets', url: 'https://www.cnbc.com/id/20910258/device/rss/rss.html' },
    { name: 'MarketWatch Pulse', url: 'https://feeds.marketwatch.com/marketwatch/marketpulse/' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Google Fed', url: 'https://news.google.com/rss/search?q=Federal+Reserve+rates+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Canada', url: 'https://news.google.com/rss/search?q=canada+economy+TSX&hl=en&gl=CA&ceid=CA:en' },
    { name: 'Financial Post', url: 'https://financialpost.com/feed/' },
  ],
  europe: [
    { name: 'CNBC Europe', url: 'https://www.cnbc.com/id/19794221/device/rss/rss.html' },
    { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/finanza.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/top-themen' },
    { name: 'Google ECB', url: 'https://news.google.com/rss/search?q=ECB+eurozone+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google EU Markets', url: 'https://news.google.com/rss/search?q=DAX+FTSE+CAC40+european+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Italy', url: 'https://news.google.com/rss/search?q=italia+economia+borsa+Milano&hl=it&gl=IT&ceid=IT:it' },
    { name: 'Google Germany', url: 'https://news.google.com/rss/search?q=germany+economy+DAX&hl=en&gl=US&ceid=US:en' },
  ],
  asia: [
    { name: 'CNBC Asia', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
    { name: 'NHK Business', url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
    { name: 'Google Nikkei', url: 'https://news.google.com/rss/search?q=nikkei+japan+economy+yen&hl=en&gl=US&ceid=US:en' },
    { name: 'Google China', url: 'https://news.google.com/rss/search?q=china+hang+seng+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Australia', url: 'https://news.google.com/rss/search?q=australia+ASX+economy+RBA&hl=en&gl=AU&ceid=AU:en' },
    { name: 'Google HK', url: 'https://news.google.com/rss/search?q=hong+kong+markets+economy&hl=en&gl=US&ceid=US:en' },
  ],
}

const REGIONS: { key: Region; label: string; emoji: string }[] = [
  { key: 'world',    label: 'Global',        emoji: '🌐' },
  { key: 'americas', label: 'North America', emoji: '🌎' },
  { key: 'europe',   label: 'Europe',        emoji: '🌍' },
  { key: 'asia',     label: 'Asia Pacific',  emoji: '🌏' },
]

const SOURCE_COLORS: Record<string, string> = {
  'Yahoo': '#7c3aed', 'MarketWatch': '#2563eb', 'CNBC': '#0ea5e9',
  'Seeking': '#f59e0b', 'Google': '#22c55e', 'Il Sole': '#ef4444',
  'Handelsblatt': '#f97316', 'NHK': '#ec4899', 'Financial Post': '#14b8a6',
}
function srcColor(s: string) {
  for (const [k, v] of Object.entries(SOURCE_COLORS)) if (s.includes(k)) return v
  return '#f97316'
}

function timeAgo(d: string) {
  if (!d) return ''
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

// Fetch RSS lato client tramite rss2json API
async function fetchFeed(name: string, url: string): Promise<NewsItem[]> {
  try {
    const api = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(url)}&count=6`
    const r = await fetch(api)
    if (!r.ok) return []
    const d = await r.json()
    if (d.status !== 'ok' || !Array.isArray(d.items)) return []
    return d.items
      .map((item: any) => ({
        title: (item.title || '').replace(/<[^>]+>/g, '').trim(),
        link: item.link || item.url || '#',
        pubDate: item.pubDate || item.published || new Date().toISOString(),
        source: name,
      }))
      .filter((item: NewsItem) => item.title.length > 10)
      .slice(0, 4)
  } catch { return [] }
}

export default function NewsPage() {
  const [news, setNews] = useState<Record<Region, NewsItem[]>>({
    world: [], americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)
  const [loadingRegion, setLoadingRegion] = useState<Region | null>(null)
  const [activeTab, setTab] = useState<Region>('world')
  const [lastUpdate, setLast] = useState<Date | null>(null)
  const [countdown, setCountdown] = useState(900)

  const loadRegion = async (region: Region) => {
    setLoadingRegion(region)
    const feeds = FEEDS[region]
    const results: NewsItem[] = []
    await Promise.all(feeds.map(async ({ name, url }) => {
      const items = await fetchFeed(name, url)
      results.push(...items)
    }))
    results.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
    // Deduplica
    const seen = new Set<string>()
    const deduped = results.filter(item => {
      const key = item.title.slice(0, 50).toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    setNews(prev => ({ ...prev, [region]: deduped.slice(0, 30) }))
    setLoadingRegion(null)
  }

  const loadAll = async () => {
    setLoading(true)
    await Promise.all(REGIONS.map(({ key }) => loadRegion(key)))
    setLast(new Date())
    setCountdown(900)
    setLoading(false)
  }

  useEffect(() => {
    loadAll()
    const timer = setInterval(loadAll, 900000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const tick = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(tick)
  }, [])

  const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  const isTabLoading = loading || loadingRegion === activeTab
  const items = news[activeTab] || []

  return (
    <div className="space-y-4 p-3 fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {lastUpdate && (
            <span style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono' }}>
              {lastUpdate.toLocaleTimeString()} · next {fmt(countdown)}
            </span>
          )}
          <button onClick={loadAll} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text4)', padding: 4 }}>
            <RefreshCw size={13} className={loading ? 'animate-spin text-gold' : ''} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{
              padding: '6px 14px', borderRadius: 4, fontSize: 12, fontWeight: 600,
              cursor: 'pointer', border: 'none', transition: 'all 0.15s',
              background: activeTab === key ? 'var(--orange)' : 'var(--surface)',
              color: activeTab === key ? '#000' : 'var(--text3)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
            {emoji} {label}
            {news[key].length > 0 && (
              <span style={{
                fontSize: 9, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                background: activeTab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: activeTab === key ? '#000' : 'var(--orange)',
              }}>{news[key].length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', minHeight: 200 }}>
        {isTabLoading ? (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--text4)' }}>
            <RefreshCw size={20} style={{ margin: '0 auto 8px', animation: 'spin 1s linear infinite', color: 'var(--orange)' }} />
            <p style={{ fontSize: 12 }}>Loading news...</p>
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--text4)', fontSize: 12 }}>
            No news available. <button onClick={() => loadRegion(activeTab)} style={{ color: 'var(--orange)', background: 'none', border: 'none', cursor: 'pointer' }}>Retry</button>
          </div>
        ) : (
          items.map((item, i) => (
            <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
              style={{
                display: 'block', padding: '10px 14px',
                background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                borderLeft: `3px solid ${srcColor(item.source)}`,
                borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                textDecoration: 'none', transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.06)')}
              onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)')}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ flex: 1, fontSize: 12, color: 'var(--text)', lineHeight: 1.55 }}>
                  {item.title}
                </div>
                <div style={{ flexShrink: 0, textAlign: 'right' }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: srcColor(item.source), fontFamily: 'IBM Plex Sans Condensed', letterSpacing: '0.04em' }}>
                    {item.source}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono', marginTop: 2 }}>
                    {timeAgo(item.pubDate)}
                  </div>
                </div>
              </div>
            </a>
          ))
        )}
      </div>

      <div style={{ fontSize: 9, color: 'var(--text4)', textAlign: 'center' }}>
        Sources: CNBC · Yahoo Finance · MarketWatch · Google News · Il Sole 24 Ore · Handelsblatt · NHK · and more · Auto-refresh every 15 min
      </div>
    </div>
  )
}
