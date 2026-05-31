'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Star, Trash2, RefreshCw } from 'lucide-react'

const fpd = (v: number | null | undefined) => {
  if (v == null || isNaN(v)) return '-'
  const n = v * 100
  return (n >= 0 ? '+' : '') + n.toFixed(1) + '%'
}
const fv = (v: number | null | undefined, d = 2) => {
  if (v == null || isNaN(v as number)) return '-'
  return (v as number).toFixed(d)
}
const clrStyle = (v: number | null | undefined) => ({
  color: v == null ? 'var(--text3)' : v >= 0 ? 'var(--green)' : 'var(--red)'
})

interface WatchStock {
  id: string
  ticker: string
  exchange: string
  company: string | null
  added_at: string
  // dati live
  price?: number | null
  change1d?: number | null
  mktCap?: number | null
  peTrail?: number | null
  peFwd?: number | null
  mom1w?: number | null
  mom1m?: number | null
  mom6m?: number | null
  mom12m?: number | null
  valueScore?: number | null
  growthScore?: number | null
  combinedRank?: number | null
  flag?: string
  sector?: string | null
}

interface Props {
  userId: string
  onSelectStock?: (s: any) => void
}

export default function MyScreen({ userId, onSelectStock }: Props) {
  const [stocks, setStocks] = useState<WatchStock[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const { data } = await supabase
      .from('watchlist')
      .select('*')
      .eq('user_id', userId)
      .order('added_at', { ascending: false })

    if (!data || data.length === 0) { setStocks([]); setLoading(false); return }

    // Carica dati live per ogni titolo
    const exchanges = data.map((s: any) => s.exchange).filter((ex: string, i: number, arr: string[]) => arr.indexOf(ex) === i)
    const liveMap: Record<string, any> = {}

    await Promise.all(exchanges.map(async (ex) => {
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

  const remove = async (id: string, ticker: string) => {
    await supabase.from('watchlist').delete().eq('id', id)
    setStocks(prev => prev.filter(s => s.id !== id))
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
        <p className="text-xs mt-1">Click the <strong>+</strong> button next to any stock to add it.</p>
      </div>
    </div>
  )

  return (
    <div className="space-y-4 fade-in">
      <div className="section-hdr flex items-center gap-2">
        <Star size={16} className="text-orange-400" />
        My Screen
        <span className="text-xs text-muted font-normal">{stocks.length} / 50</span>
        <button onClick={load} className="ml-auto text-muted hover:text-text">
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Desktop table */}
      <div className="overflow-x-auto rounded border border-border">
        <table className="data-table w-full" style={{ minWidth: 700 }}>
          <thead><tr>
            <th style={{ position: 'sticky', left: 0, background: 'var(--surface)', zIndex: 2, minWidth: 90 }}>Ticker</th>
            <th>Company</th>
            <th style={{ width: 70 }}>Price</th>
            <th style={{ width: 65 }}>1D %</th>
            <th style={{ width: 65 }}>1W %</th>
            <th style={{ width: 65 }}>1M %</th>
            <th style={{ width: 65 }}>6M %</th>
            <th style={{ width: 72 }}>12M %</th>
            <th style={{ width: 60 }}>P/E Fwd</th>
            <th style={{ width: 55 }}>Value</th>
            <th style={{ width: 55 }}>Growth</th>
            <th style={{ width: 55 }}>Best</th>
            <th style={{ width: 36 }}></th>
          </tr></thead>
          <tbody>
            {stocks.map((s) => (
              <tr key={s.id}
                onClick={() => onSelectStock?.(s)}
                className="cursor-pointer">
                <td style={{ position: 'sticky', left: 0, background: 'var(--surface)', zIndex: 1 }}>
                  <span className="font-700 text-[12px] text-orange-400 whitespace-nowrap">
                    {s.flag} {s.ticker}
                  </span>
                  <span className="text-[9px] text-muted ml-1">{s.exchange}</span>
                </td>
                <td className="text-sub text-[11px]" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {(s.company || '').slice(0, 22)}
                </td>
                <td className="font-mono text-right text-[12px]">{fv(s.price)}</td>
                <td className="font-mono text-right text-[12px]" style={clrStyle(s.change1d)}>{s.change1d != null ? fpd(s.change1d/100) : '-'}</td>
                <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1w)}>{fpd(s.mom1w)}</td>
                <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1m)}>{fpd(s.mom1m)}</td>
                <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom6m)}>{fpd(s.mom6m)}</td>
                <td className="font-mono text-right font-700 text-[12px]" style={clrStyle(s.mom12m)}>{fpd(s.mom12m)}</td>
                <td className="font-mono text-right text-[12px]">{fv(s.peFwd, 1)}</td>
                <td className="font-mono text-center text-[12px]" style={{ color: '#3b82f6' }}>{s.valueScore != null ? Math.round(s.valueScore) : '-'}</td>
                <td className="font-mono text-center text-[12px]" style={{ color: '#22c55e' }}>{s.growthScore != null ? Math.round(s.growthScore) : '-'}</td>
                <td className="font-mono text-center font-700 text-[12px]" style={{ color: 'var(--orange)' }}>{s.combinedRank != null ? Math.round(s.combinedRank) : '-'}</td>
                <td>
                  <button
                    onClick={(e) => { e.stopPropagation(); remove(s.id, s.ticker) }}
                    className="text-muted hover:text-red-400 transition-colors">
                    <Trash2 size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-muted text-right">
        {50 - stocks.length} slots remaining
      </div>
    </div>
  )
}
