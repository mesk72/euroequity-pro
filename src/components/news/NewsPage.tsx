'use client'

import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'

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
  americas: NewsItem[]
  asia: NewsItem[]
}

function timeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function NewsSection({ title, items, loading }: { title: string, items: NewsItem[], loading: boolean }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <div className="section-hdr" style={{ marginBottom: 12 }}>{title}</div>
      {loading ? (
        <div className="text-center py-8 text-muted">
          <RefreshCw size={20} className="animate-spin mx-auto mb-2 text-gold" />
          <p className="text-xs">Loading news...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="text-xs text-muted p-4">No news available.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {items.map((item, i) => (
            <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
              style={{
                display: 'block', padding: '10px 14px',
                background: i % 2 === 0 ? 'var(--surface)' : 'var(--surface2)',
                borderLeft: '3px solid var(--orange)',
                textDecoration: 'none', transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg2)')}
              onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'var(--surface)' : 'var(--surface2)')}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.5, flex: 1 }}>
                  {item.title}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, flexShrink: 0 }}>
                  <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--orange)',
                    fontFamily: 'IBM Plex Sans Condensed', letterSpacing: '0.05em' }}>
                    {item.source}
                  </span>
                  <span style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono' }}>
                    {timeAgo(item.pubDate)}
                  </span>
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export default function NewsPage() {
  const [news, setNews] = useState<NewsData>({ world: [], americas: [], europe: [], asia: [] })
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const loadNews = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/news')
      if (r.ok) {
        const d = await r.json()
        setNews(d)
        setLastUpdate(new Date())
      }
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    loadNews()
    const timer = setInterval(loadNews, 900000) // 15 minuti
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="space-y-4 p-3 fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div className="section-hdr">📰 Global Financial News</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {lastUpdate && (
            <span style={{ fontSize: 9, color: 'var(--text4)', fontFamily: 'IBM Plex Mono' }}>
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button onClick={loadNews} disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text4)' }}>
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <NewsSection title="🌐 World" items={news.world} loading={loading} />
 <NewsSection title="🌎 North America" items={news.americas} loading={loading} />
      <NewsSection title="🌍 Europe" items={news.europe} loading={loading} />
      <NewsSection title="🌏 Asia Pacific" items={news.asia} loading={loading} />

      <div style={{ fontSize: 9, color: 'var(--text4)', textAlign: 'center', paddingTop: 8, borderTop: '1px solid var(--border)' }}>
        Sources: Bloomberg · Reuters · FT · WSJ · CNBC · MarketWatch · Barron's and regional sources · Auto-refresh every 15 min
      </div>
    </div>
  )
}
