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

const FEEDS: Record<Region, { name: string; url: string }[]> = {
  world: [
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
    { name: 'Google Finance', url: 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en' },
    { name: 'Investing.com', url: 'https://www.investing.com/rss/market_overview.rss' },
  ],
  americas: [
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'CNBC Markets', url: 'https://www.cnbc.com/id/20910258/device/rss/rss.html' },
    { name: 'CNBC Earnings', url: 'https://www.cnbc.com/id/15839069/device/rss/rss.html' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
    { name: 'Google US Markets', url: 'https://news.google.com/rss/search?q=stock+market+earnings+S%26P500+nasdaq+Fed&hl=en&gl=US&ceid=US:en' },
  ],
  europe: [
    { name: 'Yahoo Finance EU', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'CNBC Europe Mkts', url: 'https://www.cnbc.com/id/19836768/device/rss/rss.html' },
    { name: 'Il Sole Mercati', url: 'https://www.ilsole24ore.com/rss/mercati.xml' },
    { name: 'Google EU Markets', url: 'https://news.google.com/rss/search?q=DAX+FTSE+CAC+eurostoxx+ECB+earnings&hl=en&gl=US&ceid=US:en' },
  ],
  asia: [
    { name: 'CNBC Asia Mkts', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
    { name: 'SCMP Markets', url: 'https://www.scmp.com/rss/92/feed' },
    { name: 'Google Asia Mkts', url: 'https://news.google.com/rss/search?q=nikkei+hangseng+ASX+stocks+earnings+asia&hl=en&gl=US&ceid=US:en' },
    { name: 'Japan Times Biz', url: 'https://www.japantimes.co.jp/feed/business/' },
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
  const [tab, setTab] = useState<Region>('world')
  const [lastUpdate, setLast] = useState('')
  const [countdown, setCountdown] = useState(900)

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

  useEffect(() => {
    const t = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(t)
  }, [])

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const items = data[tab] || []

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
            {data[key].length > 0 && (
              <span style={{
                marginLeft: 5, fontSize: 10, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
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
        ))}
      </div>
      <div style={{ fontSize: 10, color: 'var(--text4)', textAlign: 'center' }}>
        Reuters · CNBC · MarketWatch · Il Sole 24 Ore · Handelsblatt · NHK · SCMP · Auto-refresh 15 min
      </div>
    </div>
  )
}
