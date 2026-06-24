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

function timeAgo(d: string) {
  if (!d) return ''
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return m + 'm ago'
  const h = Math.floor(m / 60)
  if (h < 24) return h + 'h ago'
  return Math.floor(h / 24) + 'd ago'
}

export default function NewsPage() {
  const [allNews, setAllNews] = useState<Record<Region, NewsItem[]>>({
    world: [], americas: [], europe: [], asia: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setTab] = useState<Region>('world')

  const loadNews = async () => {
    setLoading(true)
    setError('')
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 15000)
      const r = await fetch('/api/news', {
        cache: 'no-store',
        signal: controller.signal
      })
      clearTimeout(timeout)
      if (!r.ok) throw new Error('HTTP ' + r.status)
      const d = await r.json()
      setAllNews(d)
    } catch (e: any) {
      if (e.name === 'AbortError') {
        setError('Timeout - news API taking too long')
      } else {
        setError(e.message || 'Failed to load news')
      }
    }
    setLoading(false)
  }

  useEffect(() => { loadNews() }, [])

  const items = allNews[activeTab] || []

  return (
    <div className="space-y-4 p-3 fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <button onClick={loadNews} disabled={loading}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text4)' }}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} style={{ color: loading ? 'var(--orange)' : undefined }} />
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 6, fontSize: 12, color: '#ef4444' }}>
          ❌ {error} — <button onClick={loadNews} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>Retry</button>
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
        {REGIONS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{
              padding: '6px 16px', borderRadius: 4, fontSize: 13, fontWeight: 600,
              cursor: 'pointer', border: 'none',
              background: activeTab === key ? 'var(--orange)' : 'var(--surface)',
              color: activeTab === key ? '#000' : 'var(--text3)',
            }}>
            {emoji} {label}
            {allNews[key]?.length > 0 && (
              <span style={{
                marginLeft: 6, fontSize: 10, fontWeight: 800,
                borderRadius: 10, padding: '1px 5px',
                background: activeTab === key ? 'rgba(0,0,0,0.2)' : 'rgba(249,115,22,0.15)',
                color: activeTab === key ? '#000' : 'var(--orange)',
              }}>{allNews[key].length}</span>
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
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--text4)' }}>
            <p style={{ fontSize: 14, marginBottom: 12 }}>No news for this region.</p>
            <button onClick={loadNews}
              style={{ color: 'var(--orange)', background: 'none', border: '1px solid var(--orange)', borderRadius: 4, padding: '6px 16px', cursor: 'pointer', fontSize: 13 }}>
              🔄 Refresh
            </button>
          </div>
        ) : items.map((item, i) => (
          <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
            style={{
              display: 'block', padding: '12px 16px',
              background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
              borderLeft: '3px solid var(--orange)',
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
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--orange)', fontFamily: 'IBM Plex Sans Condensed' }}>
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
        Yahoo Finance · CNBC · MarketWatch · Google News · Auto-refresh every 15 min
      </div>
    </div>
  )
}
