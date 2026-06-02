'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Star, Trash2, RefreshCw } from 'lucide-react'

const fn = (v: number | null | undefined) => {
  if (v == null || isNaN(v as number)) return '-'
  return String(Math.round(v as number))
}
const fv = (v: number | null | undefined, d = 2) => {
  if (v == null || isNaN(v as number)) return '-'
  return (v as number).toFixed(d)
}
const fpd = (v: number | null | undefined) => {
  if (v == null || isNaN(v as number)) return '-'
  const n = (v as number) * 100
  return (n >= 0 ? '+' : '') + n.toFixed(1) + '%'
}
const clrStyle = (v: number | null | undefined) => ({
  color: v == null ? 'var(--text3)' : (v as number) >= 0 ? 'var(--green)' : 'var(--red)'
})
const rankClr = (v: number | null | undefined) => {
  if (v == null) return 'var(--text3)'
  return (v as number) >= 70 ? '#22c55e' : (v as number) <= 30 ? '#e84560' : '#f59e0b'
}

const SECTOR_COLORS: Record<string, string> = {
  'Technology': '#3b82f6', 'Financials': '#f59e0b', 'Health Care': '#10b981',
  'Consumer Discretionary': '#f97316', 'Industrials': '#8b5cf6',
  'Communication Services': '#06b6d4', 'Consumer Staples': '#84cc16',
  'Energy': '#ef4444', 'Materials': '#a78bfa', 'Real Estate': '#fb7185', 'Utilities': '#34d399',
}
const getSectorColor = (s: string | null | undefined) => SECTOR_COLORS[s || ''] || '#6b7280'

interface WatchStock {
  id: string
  ticker: string
  exchange: string
  company?: string | null
  added_at: string
  flag?: string
  sector?: string | null
  country?: string | null
  price?: number | null
  change1d?: number | null
  mktCap?: number | null
  mom1w?: number | null
  mom1m?: number | null
  mom6m?: number | null
  mom12m?: number | null
  valueScore?: number | null
  growthScore?: number | null
  combinedRank?: number | null
  rankPeLtm?: number | null
  rankPeNtm?: number | null
  rankPb?: number | null
  rankEpsGr?: number | null
  rankRevGr?: number | null
}

interface Props {
  userId: string
  onSelectStock?: (s: any) => void
}

export default function MyScreen({ userId, onSelectStock }: Props) {
  const [stocks, setStocks] = useState<WatchStock[]>([])
  const [loading, setLoading] = useState(true)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const load = async () => {
    setLoading(true)
    const { data } = await supabase
      .from('watchlist')
      .select('*')
      .eq('user_id', userId)
      .order('added_at', { ascending: false })

    if (!data || data.length === 0) { setStocks([]); setLoading(false); return }

    const exchanges = data
      .map((s: any) => s.exchange)
      .filter((ex: string, i: number, arr: string[]) => arr.indexOf(ex) === i)

    const liveMap: Record<string, any> = {}
    await Promise.all(exchanges.map(async (ex: string) => {
      try {
        const r = await fetch(`/api/db/stocks?exchange=${ex}`)
        if (!r.ok) return
        const d = await r.json()
        for (const s of (d.stocks || [])) {
          liveMap[`${s.ticker}.${s.exchange}`] = s
        }
      } catch {}
    }))

    const merged = data.map((w: any) => {
      const live = liveMap[`${w.ticker}.${w.exchange}`] || {}
      return { ...w, ...live, id: w.id, added_at: w.added_at }
    })

    setStocks(merged)
    setLoading(false)
  }

  useEffect(() => { load() }, [userId])

  const remove = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await supabase.from('watchlist').delete().eq('id', id)
    setStocks(prev => prev.filter(s => s.id !== id))
  }

  // Medie equally weighted
  const avg = (field: keyof WatchStock) => {
    const vals = stocks.map(s => s[field] as number | null).filter(v => v != null && !isNaN(v as number)) as number[]
    if (vals.length === 0) return null
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }

  if (loading) return (
    <div className="p-8 text-center text-muted text-sm space-y-2">
      <RefreshCw size={20} className="animate-spin mx-auto text-gold" />
      <p>Loading My Screen...</p>
    </div>
  )

  if (stocks.length === 0) return (
    <div className="space-y-4 fade-in">
      <div className="section-hdr flex items-center gap-2">
        <Star size={16} className="text-orange-400" />
        My Screen
        <span className="text-xs text-muted font-normal">0 / 50</span>
      </div>
      <div className="p-8 text-center text-muted text-sm">
        <Star size={32} className="mx-auto mb-3 opacity-30" />
        <p>Your screen is empty.</p>
        <p className="text-xs mt-1 opacity-70">Click the <strong>+</strong> button next to any stock to add it.</p>
      </div>
    </div>
  )

  return (
    <div className="space-y-4 fade-in">
      <div className="section-hdr flex items-center gap-2">
        <Star size={16} className="text-orange-400" />
        My Screen
        <span className="text-xs text-muted font-normal">{stocks.length} / 50</span>
        <button onClick={load} className="ml-auto text-muted hover:text-text transition-colors">
          <RefreshCw size={13} />
        </button>
      </div>

      {isMobile ? (
        <div className="border border-border rounded overflow-hidden">
          <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
            Tap a stock to view details
          </div>
          {stocks.map((s) => (
            <div key={s.id}
              onClick={() => { onSelectStock?.(s); window.location.href = `/stock/${s.ticker}-${s.exchange}` }}
              className="cursor-pointer border-b border-border px-3 py-2.5 hover:bg-white/5">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-700 text-sm text-orange-400">{s.flag} {s.ticker}</span>
                  <span className="text-[9px] text-muted">{s.exchange}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-600 text-sm">{fv(s.price)}</span>
                  <span className="font-mono text-xs" style={clrStyle(s.change1d)}>
                    {s.change1d != null ? fpd(s.change1d / 100) : '-'}
                  </span>
                  <button onClick={(e) => remove(e, s.id)} className="text-muted hover:text-red-400">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-sub truncate max-w-[180px]">{s.company}</span>
                <span className="text-[9px] font-600" style={{ color: getSectorColor(s.sector) }}>{s.sector || '-'}</span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono">
                <span className="text-muted">PEv: <span style={{color: rankClr(s.rankPeLtm)}}>{fn(s.rankPeLtm)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">PEf: <span style={{color: rankClr(s.rankPeNtm)}}>{fn(s.rankPeNtm)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">EPS: <span style={{color: rankClr(s.rankEpsGr)}}>{fn(s.rankEpsGr)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Rev: <span style={{color: rankClr(s.rankRevGr)}}>{fn(s.rankRevGr)}</span></span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono mt-0.5">
                <span className="text-muted">Val: <span style={{color:'#3b82f6'}}>{fn(s.valueScore)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Grw: <span style={{color:'#22c55e'}}>{fn(s.growthScore)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Best: <span style={{color:'var(--orange)'}}>{fn(s.combinedRank)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">1M: <span style={clrStyle(s.mom1m)}>{fpd(s.mom1m)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">12M: <span style={clrStyle(s.mom12m)}>{fpd(s.mom12m)}</span></span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-border" style={{ WebkitOverflowScrolling: 'touch' }}>
          <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
            Prices delayed 15-20 min · Ranks calculated vs country universe
          </div>
          <table className="data-table" style={{ minWidth: 1000, width: 'max-content' }}>
            <thead><tr>
              <th style={{ position: 'sticky', left: 0, background: '#0d1017', zIndex: 2, minWidth: 90 }}>Ticker</th>
              <th style={{ minWidth: 130 }}>Company</th>
              <th style={{ width: 70 }}>Price</th>
              <th style={{ width: 65 }}>1D %</th>
              <th style={{ width: 75 }}>MktCap €B</th>
              <th style={{ width: 65 }}>PE LTM Rk</th>
              <th style={{ width: 65 }}>PE NTM Rk</th>
              <th style={{ width: 60 }}>PB Rk</th>
              <th style={{ width: 60 }}>EPS Rk</th>
              <th style={{ width: 60 }}>Rev Rk</th>
              <th style={{ width: 65 }}>1W %</th>
              <th style={{ width: 65 }}>1M %</th>
              <th style={{ width: 65 }}>6M %</th>
              <th style={{ width: 72 }}>12M %</th>
              <th style={{ width: 55 }}>Value</th>
              <th style={{ width: 55 }}>Growth</th>
              <th style={{ width: 55 }}>Best</th>
              <th style={{ width: 36 }}></th>
            </tr></thead>
            <tbody>
              {stocks.map((s) => (
                <tr key={s.id}
                  onClick={() => { onSelectStock?.(s); window.location.href = `/stock/${s.ticker}-${s.exchange}` }}
                  className="cursor-pointer">
                  <td style={{ position: 'sticky', left: 0, background: '#0d1017', zIndex: 1, boxShadow: '2px 0 4px rgba(0,0,0,0.3)' }}>
                    <span className="font-700 text-[12px] text-orange-400 whitespace-nowrap">{s.flag} {s.ticker}</span>
                    <span className="text-[9px] text-muted ml-1">{s.exchange}</span>
                  </td>
                  <td className="text-sub text-[11px]" style={{ maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {(s.company || '').slice(0, 20)}
                  </td>
                  <td className="font-mono text-right text-[12px]">{fv(s.price)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.change1d)}>
                    {s.change1d != null ? fpd(s.change1d / 100) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px]">{s.mktCap != null ? fv(s.mktCap, 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPeLtm)}}>{fn(s.rankPeLtm)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPeNtm)}}>{fn(s.rankPeNtm)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPb)}}>{fn(s.rankPb)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankEpsGr)}}>{fn(s.rankEpsGr)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankRevGr)}}>{fn(s.rankRevGr)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1w)}>{fpd(s.mom1w)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1m)}>{fpd(s.mom1m)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom6m)}>{fpd(s.mom6m)}</td>
                  <td className="font-mono text-right font-700 text-[12px]" style={clrStyle(s.mom12m)}>{fpd(s.mom12m)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color:'#3b82f6'}}>{fn(s.valueScore)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color:'#22c55e'}}>{fn(s.growthScore)}</td>
                  <td className="font-mono text-center font-700 text-[12px]" style={{color:'var(--orange)'}}>{fn(s.combinedRank)}</td>
                  <td onClick={(e) => remove(e, s.id)} className="cursor-pointer text-muted hover:text-red-400 transition-colors text-center">
                    <Trash2 size={13} />
                  </td>
                </tr>
              ))}
              {stocks.length > 1 && (
                <tr style={{ borderTop: '2px solid rgba(249,115,22,0.3)', background: 'rgba(249,115,22,0.04)' }}>
                  <td style={{ position: 'sticky', left: 0, background: '#120f0a', zIndex: 1, boxShadow: '2px 0 4px rgba(0,0,0,0.3)' }}>
                    <span className="font-700 text-[11px] text-orange-400">∅ Average</span>
                    <span className="text-[9px] text-muted ml-1">{stocks.length} stocks</span>
                  </td>
                  <td></td>
                  <td></td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('change1d'))}>
                    {avg('change1d') != null ? fpd((avg('change1d') as number) / 100) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px] font-700">{avg('mktCap') != null ? fv(avg('mktCap'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPeLtm'))}}>{avg('rankPeLtm') != null ? fv(avg('rankPeLtm'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPeNtm'))}}>{avg('rankPeNtm') != null ? fv(avg('rankPeNtm'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPb'))}}>{avg('rankPb') != null ? fv(avg('rankPb'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankEpsGr'))}}>{avg('rankEpsGr') != null ? fv(avg('rankEpsGr'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankRevGr'))}}>{avg('rankRevGr') != null ? fv(avg('rankRevGr'), 1) : '-'}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom1w'))}>{fpd(avg('mom1w'))}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom1m'))}>{fpd(avg('mom1m'))}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom6m'))}>{fpd(avg('mom6m'))}</td>
                  <td className="font-mono text-right font-700 text-[12px]" style={clrStyle(avg('mom12m'))}>{fpd(avg('mom12m'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color:'#3b82f6'}}>{avg('valueScore') != null ? fv(avg('valueScore'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color:'#22c55e'}}>{avg('growthScore') != null ? fv(avg('growthScore'), 1) : '-'}</td>
                  <td className="font-mono text-center font-700 text-[12px]" style={{color:'var(--orange)'}}>{avg('combinedRank') != null ? fv(avg('combinedRank'), 1) : '-'}</td>
                  <td></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-muted text-right">{50 - stocks.length} slots remaining</div>
    </div>
  )
}
