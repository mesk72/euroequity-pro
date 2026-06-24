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

// Feed RSS via rss2json - chiamata dal browser, niente CORS
const FEEDS: Record<Region, { name: string; url: string }[]> = {
  world: [
    { name: 'Reuters', url: 'https://feeds.feedburner.com/reuters/topNews' },
    { name: 'Reuters Business', url: 'https://feeds.feedburner.com/reuters/businessNews' },
    { name: 'CNBC', url: 'https://www.cnbc.com/id/10000664/device/rss/rss.html' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
  ],
  americas: [
    { name: 'CNBC Markets', url: 'https://www.cnbc.com/id/20910258/device/rss/rss.html' },
    { name: 'CNBC Economy', url: 'https://www.cnbc.com/id/20910274/device/rss/rss.html' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/marketpulse/' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Reuters Business', url: 'https://feeds.feedburner.com/reuters/businessNews' },
    { name: 'Financial Post', url: 'https://financialpost.com/feed/' },
    { name: 'Globe and Mail', url: 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/' },
  ],
  europe: [
    { name: 'CNBC Europe', url: 'https://www.cnbc.com/id/19794221/device/rss/rss.html' },
    { name: 'Reuters EU', url: 'https://feeds.feedburner.com/reuters/topNews' },
    { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/finanza.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/top-themen' },
    { name: 'Les Echos', url: 'https://www.lesechos.fr/rss/rss_finance.xml' },
    { name: 'Expansion', url: 'https://www.expansion.com/rss/mercados.xml' },
  ],
  asia: [
    { name: 'CNBC Asia', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
    { name: 'NHK', url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
    { name: 'SCMP', url: 'https://www.scmp.com/rss/92/feed' },
    { name: 'Japan Times', url: 'https://www.japantimes.co.jp/feed/' },
    { name: 'Business Times', url: 'https://www.businesstimes.com.sg/rss/top-stories' },
    { name: 'Reuters Asia', url: 'https://feeds.feedburner.com/reuters/topNews' },
  ],
}

const SRC_COLORS: Record<string, string> = {
  'Reuters': '#ef4444', 'CNBC': '#0ea5e9', 'Bloomberg': '#f59e0b',
  'Yahoo': '#7c3aed', 'MarketWatch': '#2563eb', 'WSJ': '#1d4ed8',
  'Il Sole': '#ef4444', 'Handelsblatt': '#f97316', 'NHK': '#ec4899',
  'SCMP': '#10b981', 'Japan': '#f472b6', 'Financial': '#14b8a6',
  'Seeking': '#f59e0b', 'Globe': '#06b6d4', 'Les Echos': '#8b5cf6',
}
function srcColor(s: string) {
  for (const [k, v] of Object.entries(SRC_COLORS)) if (s.includes(k)) return v
  return '#f97316'
}

function timeAgo(d: string) {
  if (!d) return ''
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return m + 'm ago'
  const h = Math.floor(m / 60)
  if (h < 24) return h + 'h ago'
  return Math.floor(h / 24) + 'd ago'
}

async function fetchFeed(name: string, url: string): Promise<NewsItem[]> {
  try {
    const api = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(url)}&count=5`
    const r = await fetch(api, { signal: AbortSignal.timeout(8000) })
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
      .slice(0, 4)
  } catch { return [] }
}

const EMPTY: Record<Region, NewsItem[]> = { world: [], americas: [], europe: [], asia: [] }

export default function NewsPage() {
  const [data, setData] = useState<Record<Region, NewsItem[]>>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Region>('world')
  const [lastUpdate, setLast] = useState<Date | null>(null)
  const [countdown, setCountdown] = useState(900)

  const loadRegion = async (region: Region): Promise<NewsItem[]> => {
    const all: NewsItem[] = []
    await Promise.all(
      FEEDS[region].map(async ({ name, url }) => {
        const items = await fetchFeed(name, url)
        all.push(...items)
      })
    )
    const seen = new Set<string>()
    return all
      .filter(n => {
        const k = n.title.slice(0, 50).toLowerCase()
        if (seen.has(k)) return false
        seen.add(k)
        return true
      })
      .sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      .slice(0, 25)
  }

  const load = async () => {
    setLoading(true)
    const [world, americas, europe, asia] = await Promise.all([
      loadRegion('world'),
      loadRegion('americas'),
      loadRegion('europe'),
      loadRegion('asia'),
    ])
    setData({ world, americas, europe, asia })
    setLast(new Date())
    setCountdown(900)
    setLoading(false)
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 900000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const tick = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(tick)
  }, [])

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const items: NewsItem[] = data[tab] || []

  return (
    <div className="space-y-4 p-3 fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {lastUpdate && (
            <span style={{ fontSize: 10, color: 'var(--text4)', fontFamily: 'IBM Plex Mono' }}>
              {lastUpdate.toLocaleTimeString()} · {fmt(countdown)}
            </span>
          )}
          <button onClick={load} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <RefreshCw size={14} style={{ color: loading ? 'var(--orange)' : 'var(--text4)', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{
              padding: '6px 16px', borderRadius: 4, fontSize: 13, fontWeight: 600,
              cursor: 'pointer', border: 'none',
              background: tab === key ? 'var(--orange)' : 'var(--surface)',
              color: tab === key ? '#000' : 'var(--text3)',
            }}>
            {emoji} {label}
            {data[key].length > 0 && (
              <span style={{
                marginLeft: 6, fontSize: 10, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                background: tab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: tab === key ? '#000' : 'var(--orange)',
              }}>{data[key].length}</span>
            )}
          </button>
        ))}
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', minHeight: 200 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <RefreshCw size={24} style={{ margin: '0 auto 12px', animation: 'spin 1s linear infinite', color: 'var(--orange)' }} />
            <p style={{ fontSize: 13, color: 'var(--text4)' }}>Loading news from Reuters, CNBC, Yahoo Finance...</p>
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <p style={{ fontSize: 14, color: 'var(--text4)', marginBottom: 12 }}>No news available.</p>
            <button onClick={load} style={{ color: 'var(--orange)', background: 'none', border: '1px solid var(--orange)', borderRadius: 4, padding: '6px 16px', cursor: 'pointer', fontSize: 13 }}>
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
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <div style={{ flex: 1, fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>
                {item.title}
              </div>
              <div style={{ flexShrink: 0, textAlign: 'right', minWidth: 90 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: srcColor(item.source), fontFamily: 'IBM Plex Sans Condensed' }}>
                  {item.source}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text4)', marginTop: 2 }}>
                  {timeAgo(item.pubDate)}
                </div>
              </div>
            </div>
          </a>
        ))}
      </div>

      <div style={{ fontSize: 10, color: 'var(--text4)', textAlign: 'center' }}>
        Reuters · CNBC · Yahoo Finance · MarketWatch · Il Sole 24 Ore · Handelsblatt · NHK · SCMP · Auto-refresh every 15 min
      </div>
    </div>
  )
}
