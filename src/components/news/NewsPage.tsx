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

const SRC_COLORS: Record<string, string> = {
  'Bloomberg': '#f59e0b', 'Reuters': '#ef4444', 'CNBC': '#0ea5e9',
  'Yahoo': '#7c3aed', 'MarketWatch': '#2563eb', 'WSJ': '#1d4ed8',
  'FT': '#f97316', 'Financial Times': '#f97316', 'Seeking': '#f59e0b',
  'Il Sole': '#ef4444', 'Handelsblatt': '#f97316', 'NHK': '#ec4899',
  'Google': '#22c55e', 'Financial Post': '#14b8a6',
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

const EMPTY: Record<Region, NewsItem[]> = { world: [], americas: [], europe: [], asia: [] }

export default function NewsPage() {
  const [data, setData] = useState<Record<Region, NewsItem[]>>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Region>('world')
  const [lastUpdate, setLast] = useState<Date | null>(null)
  const [countdown, setCountdown] = useState(900)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/news', { cache: 'no-store' })
      if (!res.ok) throw new Error('HTTP ' + res.status)
      const json = await res.json()
      setData({
        world:    Array.isArray(json.world)    ? json.world    : [],
        americas: Array.isArray(json.americas) ? json.americas : [],
        europe:   Array.isArray(json.europe)   ? json.europe   : [],
        asia:     Array.isArray(json.asia)     ? json.asia     : [],
      })
      setLast(new Date())
      setCountdown(900)
    } catch (e: any) {
      setError(e.message || 'Error loading news')
    }
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
              {lastUpdate.toLocaleTimeString()} · next {fmt(countdown)}
            </span>
          )}
          <button onClick={load} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <RefreshCw size={14} style={{ color: loading ? 'var(--orange)' : 'var(--text4)', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: 10, background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 6, fontSize: 12, color: '#ef4444', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          ❌ {error}
          <button onClick={load} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline', fontSize: 12 }}>Retry</button>
        </div>
      )}

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
            <p style={{ fontSize: 13, color: 'var(--text4)' }}>Loading news...</p>
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
        Sources: Bloomberg · Reuters · CNBC · Yahoo Finance · MarketWatch · WSJ · FT · Il Sole 24 Ore · Handelsblatt · NHK · Google News · Auto-refresh every 15 min
      </div>
    </div>
  )
}
