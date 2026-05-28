'use client'

import { useEffect, useState, useRef } from 'react'
import { SECTOR_COLORS } from '@/lib/constants'
import { Stock } from '@/lib/ranking'

interface SectorData {
  sector:    string
  count:     number
  mcwReturn: number  // market-cap weighted return
  totalMktCap: number
  stocks:    Stock[]
}

interface Props {
  stocks:          Stock[]
  onSectorClick:   (sector: string) => void
}

function computeSectors(stocks: Stock[]): SectorData[] {
  const map = new Map<string, Stock[]>()
  for (const s of stocks) {
    const sec = s.sector || 'Other'
    if (!map.has(sec)) map.set(sec, [])
    map.get(sec)!.push(s)
  }

  const result: SectorData[] = []
  for (const [sector, ss] of Array.from(map.entries())) {
    const valid = ss.filter(s => s.mktCap && s.change1d != null)
    const totalMkt = valid.reduce((a, s) => a + (s.mktCap || 0), 0)
    const mcwReturn = totalMkt > 0
      ? valid.reduce((a, s) => a + (s.change1d || 0) * (s.mktCap || 0), 0) / totalMkt
      : 0
    result.push({ sector, count: ss.length, mcwReturn, totalMktCap: totalMkt, stocks: ss })
  }

  return result.sort((a, b) => b.totalMktCap - a.totalMktCap)
}

function getColor(ret: number): string {
  if (ret > 2)    return '#16a34a'
  if (ret > 1)    return '#22d48a'
  if (ret > 0.5)  return '#4ade80'
  if (ret > 0)    return '#86efac'
  if (ret > -0.5) return '#fca5a5'
  if (ret > -1)   return '#f87171'
  if (ret > -2)   return '#ef4444'
  return '#dc2626'
}

function getTextColor(ret: number): string {
  return Math.abs(ret) > 0.5 ? '#ffffff' : '#1f2937'
}

export default function SectorHeatmap({ stocks, onSectorClick }: Props) {
  const sectors = computeSectors(stocks)
  const maxMkt  = Math.max(...sectors.map(s => s.totalMktCap), 1)

  return (
    <div>
      <div className="section-hdr mb-4">
        🏭 Sector Heatmap — Market Cap Weighted Return (Top 600)
      </div>
      <p className="text-xs text-muted mb-3">
        Size = total market cap · Color = today's MCW return · Click to open sector screen
      </p>
      <div
        style={{
          display:  'flex',
          flexWrap: 'wrap',
          gap:      '6px',
          alignItems: 'flex-start',
        }}
      >
        {sectors.map(sec => {
          // Size proportional to market cap (min 80px, max 280px)
          const ratio = sec.totalMktCap / maxMkt
          const size  = Math.max(80, Math.min(280, Math.round(ratio * 280)))
          const bg    = getColor(sec.mcwReturn)
          const tc    = getTextColor(sec.mcwReturn)
          const sign  = sec.mcwReturn >= 0 ? '+' : ''

          return (
            <button
              key={sec.sector}
              onClick={() => onSectorClick(sec.sector)}
              style={{
                width:         size,
                height:        size,
                backgroundColor: bg,
                borderRadius:  '6px',
                border:        'none',
                cursor:        'pointer',
                display:       'flex',
                flexDirection: 'column',
                alignItems:    'center',
                justifyContent:'center',
                padding:       '8px',
                transition:    'transform 0.15s, opacity 0.15s',
                position:      'relative',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1.04)'
                ;(e.currentTarget as HTMLElement).style.opacity  = '0.9'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1)'
                ;(e.currentTarget as HTMLElement).style.opacity  = '1'
              }}
              title={`${sec.sector}: ${sign}${sec.mcwReturn.toFixed(2)}% · ${sec.count} stocks · €${sec.totalMktCap.toFixed(0)}B`}
            >
              <span style={{
                color:      tc,
                fontSize:   size > 120 ? '12px' : '10px',
                fontWeight: 700,
                textAlign:  'center',
                lineHeight: 1.2,
                marginBottom: '4px',
              }}>
                {sec.sector}
              </span>
              <span style={{
                color:      tc,
                fontSize:   size > 120 ? '16px' : '13px',
                fontFamily: 'Fira Code, monospace',
                fontWeight: 600,
              }}>
                {sign}{sec.mcwReturn.toFixed(2)}%
              </span>
              <span style={{
                color:      tc,
                fontSize:   '10px',
                opacity:    0.8,
                marginTop:  '2px',
              }}>
                {sec.count} stocks
              </span>
              {size > 140 && (
                <span style={{
                  color:    tc,
                  fontSize: '9px',
                  opacity:  0.7,
                  marginTop:'2px',
                }}>
                  €{sec.totalMktCap.toFixed(0)}B
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 text-xs text-muted">
        <span>Today's MCW return:</span>
        {[
          { label: '>+2%',  color: '#16a34a' },
          { label: '+1%',   color: '#22d48a' },
          { label: '0%',    color: '#86efac' },
          { label: '-1%',   color: '#f87171' },
          { label: '<-2%',  color: '#dc2626' },
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
