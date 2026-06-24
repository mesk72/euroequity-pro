'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, ExternalLink, Globe, Clock } from 'lucide-react'

interface NewsItem {
  title: string
  link: string
  pubDate: string
  source: string
}

interface NewsData {
  world: NewsItem[]
  americas: NewsItem[]
  europe: NewsItem[]
  asia: NewsItem[]
}

type Region = 'world' | 'americas' | 'europe' | 'asia'

function timeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

const SOURCE_COLOR: Record<string, string> = {
  'Bloomberg': '#f59e0b', 'Reuters': '#ef4444', 'FT': '#f97316',
  'WSJ': '#3b82f6', 'CNBC': '#06b6d4', 'MarketWatch': '#8b5cf6',
  'Yahoo Finance': '#a78bfa', 'Il Sole 24 Ore': '#22c55e',
  'Handelsblatt': '#fbbf24', 'SCMP': '#34d399', 'Japan Times': '#f472b6',
  'NHK': '#fb7185', 'default': '#f97316'
}

function getSourceColor(source: string) {
  for (const [key, color] of Object.entries(SOURCE_COLOR)) {
    if (source.includes(key)) return color
  }
  return SOURCE_COLOR.default
}

const REGIONS: { key: Region; label: string; emoji: string }[] = [
  { key: 'world',    label: 'Global',        emoji: '🌐' },
  { key: 'americas', label: 'North America', emoji: '🌎' },
  { key: 'europe',   label: 'Europe',        emoji: '🌍' },
  { key: 'asia',     label: 'Asia Pacific',  emoji: '🌏' },
]

function NewsSection({ items, loading }: { items: NewsItem[], loading: boolean }) {
  if (loading) return (
    <div className="text-center py-12 text-muted">
      <RefreshCw size={20} className="animate-spin mx-auto mb-2 text-gold" />
      <p className="text-xs">Loading news...</p>
    </div>
  )
  if (items.length === 0) return (
    <div className="text-xs text-muted p-4 text-center">No news available.</div>
  )
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {items.map((item, i) => (
        <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
          style={{
            display: 'block', padding: '10px 14px',
            background: i % 2 === 0 ? 'var(--surface)' : 'rgba(255,255,255,0.02)',
            borderLeft: `3px solid ${getSourceColor(item.source)}`,
            textDecoration: 'none', transition: 'background 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.06)')}
          onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'var(--surface)' : 'rgba(255,255,255,0.02)')}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
            <div style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.55, flex: 1 }}>
              {item.title}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3, flexShrink: 0 }}>
              <span style={{
                fontSize: 9, fontWeight: 700, letterSpacing: '0.04em',
                fontFamily: 'IBM Plex Sans Condensed',
                color: getSourceColor(item.source)
              }}>
                {item.source}
              </span>
              <span style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono', display: 'flex', alignItems: 'center', gap: 3 }}>
                <Clock size={8} />
                {timeAgo(item.pubDate)}
              </span>
            </div>
          </div>
        </a>
      ))}
    </div>
  )
}

export default function NewsPage() {
  const [news, setNews]         = useState<NewsData>({ world: [], americas: [], europe: [], asia: [] })
  const [loading, setLoading]   = useState(true)
  const [lastUpdate, setLast]   = useState<Date | null>(null)
  const [activeTab, setTab]     = useState<Region>('world')
  const [countdown, setCountdown] = useState(900)

  const loadNews = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/news')
      if (r.ok) { setNews(await r.json()); setLast(new Date()); setCountdown(900) }
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    loadNews()
    const timer = setInterval(loadNews, 900000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const tick = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 900), 1000)
    return () => clearInterval(tick)
  }, [])

  const fmt = (s: number) => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`

  return (
    <div className="space-y-4 p-3 fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {lastUpdate && (
            <span style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono' }}>
              Updated {lastUpdate.toLocaleTimeString()} · refresh in {fmt(countdown)}
            </span>
          )}
          <button onClick={loadNews} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text4)', padding: 4 }}>
            <RefreshCw size={13} className={loading ? 'animate-spin text-gold' : ''} />
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => {
          const count = news[key]?.length || 0
          return (
            <button key={key} onClick={() => setTab(key)}
              style={{
                padding: '6px 14px', borderRadius: 4, fontSize: 12, fontWeight: 600,
                cursor: 'pointer', border: 'none', transition: 'all 0.15s',
                background: activeTab === key ? 'var(--orange)' : 'var(--surface)',
                color: activeTab === key ? '#000' : 'var(--text3)',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
              {emoji} {label}
              {count > 0 && (
                <span style={{
                  fontSize: 9, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                  background: activeTab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                  color: activeTab === key ? '#000' : 'var(--orange)',
                }}>
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* News content */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden' }}>
        <NewsSection items={news[activeTab] || []} loading={loading} />
      </div>

      {/* Footer */}
      <div style={{ fontSize: 9, color: 'var(--text4)', textAlign: 'center', paddingTop: 4 }}>
        Sources: Bloomberg · Reuters · FT · WSJ · CNBC · MarketWatch · Yahoo Finance · Il Sole 24 Ore · Handelsblatt · SCMP · Japan Times · NHK · and more · Auto-refresh every 15 min
      </div>
    </div>
  )
}
