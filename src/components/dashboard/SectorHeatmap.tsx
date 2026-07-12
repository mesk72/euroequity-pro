'use client'

import { useState } from 'react'
import { SECTOR_COLORS } from '@/lib/constants'
import { Stock } from '@/lib/ranking'

interface SectorData {
  sector: string
  count: number
  mcwReturn: number
  totalMktCap: number
}

interface Props {
  stocks: Stock[]
  onSectorClick: (sector: string) => void
}

type Period = '1d' | '1w' | '1m' | '6m' | '12m'

const PERIOD_FIELD: Record<Period, string> = {
  '1d': 'change1d',
  '1w': 'mom1w',
  '1m': 'mom1m',
  '6m': 'mom6m',
  '12m': 'mom12m',
}

const PERIOD_LABEL: Record<Period, string> = {
  '1d': '1 Day',
  '1w': '1 Week',
  '1m': '1 Month',
  '6m': '6 Months',
  '12m': '12 Months',
}

function computeSectors(stocks: Stock[], field: string): SectorData[] {
  const map = new Map<string, Stock[]>()
  for (const s of stocks) {
    const sec = s.sector || 'Other'
    if (!map.has(sec)) map.set(sec, [])
    map.get(sec)!.push(s)
  }
  const result: SectorData[] = []
  for (const [sector, ss] of Array.from(map.entries())) {
    const valid = ss.filter(s => s.mktCap && (s as any)[field] != null)
    // Peso di visualizzazione (dimensione del riquadro): market cap ATTUALE,
    // rappresenta quanto e' grande il settore oggi — corretto per questo scopo.
    const totalMkt = valid.reduce((a, s) => a + (s.mktCap || 0), 0)

    // Peso per il calcolo del rendimento: market cap di PARTENZA stimata
    // (cap_oggi / (1 + rendimento)), non quella attuale. Usare la cap
    // attuale crea un bias circolare — i titoli che sono saliti di piu'
    // pesano di piu' proprio perche' sono saliti, gonfiando ulteriormente
    // la media a loro favore. Piu' il periodo e' lungo, piu' l'effetto e'
    // marcato (es. un titolo +2900% pesa oggi ~30x quanto pesava un anno fa).
    let weightedSum = 0
    let startMktTotal = 0
    for (const s of valid) {
      const ret = (s as any)[field] || 0
      const currentCap = s.mktCap || 0
      const startCap = (1 + ret) > 0 ? currentCap / (1 + ret) : currentCap
      weightedSum += ret * startCap
      startMktTotal += startCap
    }
    const multiplier = 100
    const mcwReturn = startMktTotal > 0 ? (weightedSum / startMktTotal) * multiplier : 0
    result.push({ sector, count: ss.length, mcwReturn, totalMktCap: totalMkt })
  }
  return result.sort((a, b) => b.totalMktCap - a.totalMktCap)
}

function getColor(ret: number): string {
  if (ret > 2) return '#16a34a'
  if (ret > 1) return '#22d48a'
  if (ret > 0.5) return '#4ade80'
  if (ret > 0) return '#86efac'
  if (ret > -0.5) return '#fca5a5'
  if (ret > -1) return '#f87171'
  if (ret > -2) return '#ef4444'
  return '#dc2626'
}

function getTextColor(ret: number): string {
  return Math.abs(ret) > 0.5 ? '#ffffff' : '#1f2937'
}

export default function SectorHeatmap({ stocks, onSectorClick }: Props) {
  const [period, setPeriod] = useState<Period>('1d')
  const field = PERIOD_FIELD[period]
  const sectors = computeSectors(stocks, field)
  const maxMkt = Math.max(...sectors.map(s => s.totalMktCap), 1)

  return (
    <div>
      {/* Period selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700 }}>
          Period:
        </span>
        {(Object.keys(PERIOD_LABEL) as Period[]).map(p => (
          <button key={p} onClick={() => setPeriod(p)}
            style={{
              fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 11,
              padding: '4px 10px', borderRadius: 3, cursor: 'pointer',
              border: `1px solid ${period === p ? 'var(--orange)' : 'var(--border)'}`,
              background: period === p ? 'var(--orange)' : 'transparent',
              color: period === p ? '#000' : 'var(--text4)'
            }}>
            {PERIOD_LABEL[p]}
          </button>
        ))}
      </div>

      {/* Heatmap */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'flex-start' }}>
        {sectors.map(sec => {
          const ratio = sec.totalMktCap / maxMkt
          const size = Math.max(80, Math.min(280, Math.round(ratio * 280)))
          const bg = getColor(sec.mcwReturn)
          const tc = getTextColor(sec.mcwReturn)
          const sign = sec.mcwReturn >= 0 ? '+' : ''
          return (
            <button key={sec.sector} onClick={() => onSectorClick(sec.sector)}
              style={{
                width: size, height: size, backgroundColor: bg,
                borderRadius: '6px', border: 'none', cursor: 'pointer',
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                padding: '8px', transition: 'transform 0.15s, opacity 0.15s',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1.04)'
                ;(e.currentTarget as HTMLElement).style.opacity = '0.9'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1)'
                ;(e.currentTarget as HTMLElement).style.opacity = '1'
              }}
              title={`${sec.sector}: ${sign}${sec.mcwReturn.toFixed(2)}% · ${sec.count} stocks`}
            >
              <span style={{ color: tc, fontSize: size > 120 ? '12px' : '10px', fontWeight: 700, textAlign: 'center', lineHeight: 1.2, marginBottom: '4px' }}>
                {sec.sector}
              </span>
              <span style={{ color: tc, fontSize: size > 120 ? '16px' : '13px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 600 }}>
                {sign}{sec.mcwReturn.toFixed(2)}%
              </span>
              <span style={{ color: tc, fontSize: '10px', opacity: 0.8, marginTop: '2px' }}>
                {sec.count} stocks
              </span>
              {size > 140 && (
                <span style={{ color: tc, fontSize: '9px', opacity: 0.7, marginTop: '2px' }}>
                  ${sec.totalMktCap.toFixed(0)}B
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 text-xs text-muted">
        <span>MCW Return ({PERIOD_LABEL[period]}):</span>
        {[
          { label: '>+2%', color: '#16a34a' },
          { label: '+1%', color: '#22d48a' },
          { label: '0%', color: '#86efac' },
          { label: '-1%', color: '#f87171' },
          { label: '<-2%', color: '#dc2626' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1">
            <div style={{ width: 12, height: 12, borderRadius: 2, background: color }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
