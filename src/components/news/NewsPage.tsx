'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, Clock } from 'lucide-react'

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

function timeAgo(d: string) {
  if (!d) return ''
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return m + 'm ago'
  const h = Math.floor(m / 60)
  if (h < 24) return h + 'h ago'
  return Math.floor(h / 24) + 'd ago'
}

const SRC_COLORS: Record<string, string> = {
  'Yahoo': '#7c3aed', 'CNBC': '#0ea5e9', 'Reuters': '#ef4444',
  'MarketWatch': '#2563eb', 'Bloomberg': '#f59e0b', 'Seeking': '#f59e0b',
  'Google': '#22c55e', 'Il Sole': '#ef4444', 'Handelsblatt': '#f97316',
  'NHK': '#ec4899', 'Financial Post': '#14b8a6',
}
function srcColor(s: string) {
  for (const [k, v] of Object.entries(SRC_COLORS)) if (s.includes(k)) return v
  return '#f97316'
}

export default function NewsPage() {
  const [news, setNews] = useState<Record<Region, NewsItem[]>>({
    world: [], americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLast] = useState<Date | null>(null)
  const [activeTab, setTab] = useState<Region>('world')
  const [countdown, setCountdown] = useState(900)

  const loadNews = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/news')
      if (r.ok) {
        const d = await r.json()
        setNews(d)
        setLast(new Date())
        setCountdown(900)
      }
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    loadNews()
    const timer = setInterval(loadNews, 900000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const tick = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000)
    return () => clearInterval(tick)
  }, [])

  const fmt = (s: number) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0')
  const items = news[activeTab] || []

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
          <button onClick={loadNews} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text4)' }}>
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} style={{ color: loading ? 'var(--orange)' : undefined }} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{
              padding: '6px 16px', borderRadius: 4, fontSize: 13, fontWeight: 600,
              cursor: 'pointer', border: 'none', transition: 'all 0.15s',
              background: activeTab === key ? 'var(--orange)' : 'var(--surface)',
              color: activeTab === key ? '#000' : 'var(--text3)',
            }}>
            {emoji} {label}
            {news[key].length > 0 && (
              <span style={{
                marginLeft: 6, fontSize: 10, fontWeight: 800, borderRadius: 10, padding: '1px 5px',
                background: activeTab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: activeTab === key ? '#000' : 'var(--orange)',
              }}>{news[key].length}</span>
            )}
          </button>
        ))}
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', minHeight: 300 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 64, color: 'var(--text4)' }}>
            <RefreshCw size={24} style={{ margin: '0 auto 12px', animation: 'spin 1s linear infinite', color: 'var(--orange)' }} />
            <p style={{ fontSize: 13 }}>Loading news...</p>
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 64, color: 'var(--text4)', fontSize: 13 }}>
            No news available.{' '}
            <button onClick={loadNews} style={{ color: 'var(--orange)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>
              Retry
            </button>
          </div>
        ) : (
          items.map((item, i) => (
            <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
              style={{
                display: 'block', padding: '12px 16px',
                background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                borderLeft: '3px solid ' + srcColor(item.source),
                borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                textDecoration: 'none', transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.06)')}
              onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)')}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ flex: 1, fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>
                  {item.title}
                </div>
                <div style={{ flexShrink: 0, textAlign: 'right', minWidth: 80 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: srcColor(item.source), fontFamily: 'IBM Plex Sans Condensed' }}>
                    {item.source}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text4)', marginTop: 2 }}>
                    {timeAgo(item.pubDate)}
                  </div>
                </div>
              </div>
            </a>
          ))
        )}
      </div>

      <div style={{ fontSize: 10, color: 'var(--text4)', textAlign: 'center' }}>
        Sources: Yahoo Finance · CNBC · MarketWatch · Google News · and more · Auto-refresh every 15 min
      </div>
    </div>
  )
}
