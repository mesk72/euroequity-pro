'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { computeScores } from '@/lib/ranking'
import { DEMO_STOCKS } from '@/lib/demoData'
import { SECTOR_COLORS } from '@/lib/constants'

function fp(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return 'NA'
  return `${(v as number) >= 0 ? '+' : ''}${(v as number).toFixed(d)}%`
}
function fv(v?: number | null, d = 1): string {
  if (v == null || isNaN(v as number)) return 'NA'
  return (v as number).toFixed(d)
}

interface SectorData {
  sector:      string
  count:       number
  totalMktCap: number
  avgChange1d: number | null
  avgMom1w:    number | null
  avgMom1m:    number | null
  avgMom6m:    number | null
  avgMom12m:   number | null
  avgPeFwd:    number | null
  avgPb:       number | null
  avgRoe:      number | null
  avgDivYield: number | null
  avgValueScore:  number | null
  avgGrowthScore: number | null
  stocks:      any[]
}

function avg(arr: (number | null | undefined)[]): number | null {
  const v = arr.filter(x => x != null && !isNaN(x as number)) as number[]
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
}

function wAvg(stocks: any[], field: string): number | null {
  const valid = stocks.filter(s => s[field] != null && s.mktCap != null && s.mktCap > 0)
  const sumW  = valid.reduce((a: number, s: any) => a + s.mktCap, 0)
  if (!sumW) return avg(stocks.map(s => s[field]))
  return valid.reduce((a: number, s: any) => a + s[field] * s.mktCap, 0) / sumW
}

export default function SectorsPage() {
  const router = useRouter()
  const [selected, setSelected] = useState<string | null>(null)
  const [sortKey,  setSortKey]  = useState<keyof SectorData>('totalMktCap')
  const [sortAsc,  setSortAsc]  = useState(false)

  const allStocks = useMemo(() => computeScores([...DEMO_STOCKS]), [])

  const sectors: SectorData[] = useMemo(() => {
    const map: Record<string, any[]> = {}
    for (const s of allStocks) {
      const sec = s.sector || 'Other'
      if (!map[sec]) map[sec] = []
      map[sec].push(s)
    }
    return Object.entries(map).map(([sector, stocks]) => ({
      sector,
      count:       stocks.length,
      totalMktCap: stocks.reduce((a, s) => a + (s.mktCap || 0), 0),
      avgChange1d: wAvg(stocks, 'change1d'),
      avgMom1w:    wAvg(stocks, 'mom1w'),
      avgMom1m:    wAvg(stocks, 'mom1m'),
      avgMom6m:    wAvg(stocks, 'mom6m'),
      avgMom12m:   wAvg(stocks, 'mom12m'),
      avgPeFwd:    avg(stocks.map(s => s.peFwd)),
      avgPb:       avg(stocks.map(s => s.pb)),
      avgRoe:      avg(stocks.map(s => s.roe)),
      avgDivYield: avg(stocks.map(s => s.divYield)),
      avgValueScore:  avg(stocks.map(s => s.valueScore)),
      avgGrowthScore: avg(stocks.map(s => s.growthScore)),
      stocks,
    }))
  }, [allStocks])

  const sorted = [...sectors].sort((a, b) => {
    const av = a[sortKey] as any
    const bv = b[sortKey] as any
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    return sortAsc ? av - bv : bv - av
  })

  const toggle = (key: keyof SectorData) => {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const selectedSector = selected ? sectors.find(s => s.sector === selected) : null

  const totalMktCap = sectors.reduce((a, s) => a + s.totalMktCap, 0)

  return (
    <div style={{ background:'var(--bg)', minHeight:'100vh', fontFamily:'IBM Plex Sans, sans-serif', fontSize:13 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&display=swap');
        :root {
          --bg:#0a0e1a; --bg2:#0d1221; --surface:#111827; --surface2:#161d2e;
          --border:#1e2d45; --orange:#f97316; --green:#22c55e; --red:#ef4444;
          --gold:#eab308; --text:#ffffff; --text2:#e2e8f0; --text3:#cbd5e1; --text4:#94a3b8;
        }
        body { background:var(--bg); margin:0; color:var(--text); }
        * { box-sizing:border-box; }
        th { background:var(--surface2); color:var(--text4); font-family:'IBM Plex Sans Condensed',sans-serif;
          font-size:10px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
          padding:7px 10px; text-align:left; border-bottom:2px solid var(--border);
          white-space:nowrap; cursor:pointer; user-select:none; }
        th:hover { color:var(--orange); }
        td { padding:7px 10px; border-bottom:1px solid rgba(30,45,69,0.5); }
        tr:hover td { background:rgba(249,115,22,0.04); cursor:pointer; }
      `}</style>

      {/* Nav */}
      <div style={{ background:'var(--surface)', borderBottom:'2px solid var(--orange)',
        padding:'0 24px', height:44, display:'flex', alignItems:'center', gap:16 }}>
        <button onClick={() => router.push('/')}
          style={{ display:'flex', alignItems:'center', gap:6, color:'var(--text4)',
            background:'none', border:'none', cursor:'pointer', fontSize:13 }}>
          <ArrowLeft size={15} /> Back
        </button>
        <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:18, color:'var(--orange)' }}>
          EURO<span style={{ color:'var(--text3)' }}>EQUITY</span> PRO
        </div>
      </div>

      <div style={{ maxWidth:1200, margin:'0 auto', padding:'24px 16px' }}>

        {/* Header */}
        <div style={{ marginBottom:20 }}>
          <h1 style={{ margin:'0 0 6px', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:28 }}>
            🏭 Sector Analysis — Eurozone
          </h1>
          <div style={{ fontSize:13, color:'var(--text3)' }}>
            Market-cap weighted performance and fundamentals by sector · {allStocks.length} stocks
          </div>
        </div>

        {/* Heatmap visuale */}
        <div style={{ display:'flex', flexWrap:'wrap', gap:8, marginBottom:24, padding:16,
          background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4 }}>
          <div style={{ width:'100%', fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
            letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)', marginBottom:8 }}>
            Sector Heatmap — 1D Market Cap Weighted Return
          </div>
          {[...sectors].sort((a,b) => b.totalMktCap - a.totalMktCap).map(sec => {
            const ret = sec.avgChange1d || 0
            const pct = sec.totalMktCap / (totalMktCap || 1)
            const size = Math.max(70, Math.min(220, Math.round(pct * 220 * 8)))
            const bg = ret > 2 ? '#16a34a' : ret > 1 ? '#22c55e' : ret > 0.3 ? '#4ade80'
              : ret > 0 ? '#86efac' : ret > -0.3 ? '#fca5a5' : ret > -1 ? '#f87171'
              : ret > -2 ? '#ef4444' : '#dc2626'
            const tc = Math.abs(ret) > 0.5 ? '#fff' : '#111'
            const color = SECTOR_COLORS[sec.sector] || '#6b7280'
            return (
              <div key={sec.sector}
                onClick={() => setSelected(selected === sec.sector ? null : sec.sector)}
                style={{ width:size, height:size, background:bg, borderRadius:4,
                  border:`2px solid ${selected === sec.sector ? 'var(--orange)' : 'rgba(255,255,255,0.1)'}`,
                  cursor:'pointer', display:'flex', flexDirection:'column',
                  alignItems:'center', justifyContent:'center', padding:6,
                  transition:'transform 0.12s', position:'relative' }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.transform = 'scale(1.04)'}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.transform = 'scale(1)'}>
                <span style={{ fontSize: size > 100 ? 11 : 9, fontFamily:'IBM Plex Sans Condensed',
                  fontWeight:700, color:tc, textAlign:'center', lineHeight:1.2, marginBottom:3 }}>
                  {sec.sector}
                </span>
                <span style={{ fontSize: size > 100 ? 14 : 11, fontFamily:'IBM Plex Mono',
                  fontWeight:700, color:tc }}>
                  {ret >= 0 ? '+' : ''}{ret.toFixed(1)}%
                </span>
                {size > 100 && (
                  <span style={{ fontSize:9, color:tc, opacity:0.8 }}>{sec.count} stocks</span>
                )}
              </div>
            )
          })}
        </div>

        {/* Dettaglio settore selezionato */}
        {selectedSector && (
          <div style={{ background:'var(--surface)', border:`1px solid var(--border)`,
            borderLeft:`3px solid ${SECTOR_COLORS[selectedSector.sector] || 'var(--orange)'}`,
            borderRadius:'0 4px 4px 0', padding:16, marginBottom:16 }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
              <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:18,
                color: SECTOR_COLORS[selectedSector.sector] || 'var(--orange)' }}>
                {selectedSector.sector}
              </div>
              <button onClick={() => setSelected(null)}
                style={{ color:'var(--text4)', background:'none', border:'none', cursor:'pointer', fontSize:18 }}>×</button>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:12 }}>
              {[
                ['Stocks', selectedSector.count.toString()],
                ['Mkt Cap €B', (selectedSector.totalMktCap).toFixed(0)],
                ['1D Return', fp(selectedSector.avgChange1d)],
                ['12M Return', fp(selectedSector.avgMom12m)],
                ['Avg P/E Fwd', fv(selectedSector.avgPeFwd)],
                ['Avg P/B', fv(selectedSector.avgPb, 2)],
                ['Avg ROE %', fp(selectedSector.avgRoe)],
                ['Avg Div %', fp(selectedSector.avgDivYield)],
              ].map(([label, value]) => (
                <div key={label} style={{ background:'var(--bg2)', borderRadius:3, padding:'8px 10px' }}>
                  <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                    letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--text4)', marginBottom:3 }}>
                    {label}
                  </div>
                  <div style={{ fontFamily:'IBM Plex Mono', fontWeight:600, fontSize:14, color:'var(--text)' }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
            {/* Top 5 titoli del settore */}
            <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--text4)', marginBottom:8 }}>
              Top stocks by market cap
            </div>
            <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
              {[...selectedSector.stocks]
                .sort((a,b) => (b.mktCap||0)-(a.mktCap||0))
                .slice(0, 6)
                .map(s => (
                  <div key={s.ticker}
                    onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                    style={{ background:'var(--bg2)', border:'1px solid var(--border)',
                      borderRadius:3, padding:'6px 12px', cursor:'pointer',
                      display:'flex', alignItems:'center', gap:8 }}>
                    <span style={{ fontSize:14 }}>{s.flag}</span>
                    <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)' }}>{s.ticker}</span>
                    <span style={{ fontFamily:'IBM Plex Mono', fontSize:11,
                      color: (s.change1d||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      {fp(s.change1d)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Tabella settori */}
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, overflow:'hidden' }}>
          <div style={{ overflowX:'auto' }}>
            <table>
              <thead>
                <tr>
                  <th onClick={() => toggle('sector')}>Sector</th>
                  <th onClick={() => toggle('count')}># Stocks</th>
                  <th onClick={() => toggle('totalMktCap')}>Mkt Cap €B</th>
                  <th onClick={() => toggle('avgChange1d')}>1D %</th>
                  <th onClick={() => toggle('avgMom1w')}>1W %</th>
                  <th onClick={() => toggle('avgMom1m')}>1M %</th>
                  <th onClick={() => toggle('avgMom6m')}>6M %</th>
                  <th onClick={() => toggle('avgMom12m')}>12M %</th>
                  <th onClick={() => toggle('avgPeFwd')}>P/E Fwd</th>
                  <th onClick={() => toggle('avgPb')}>P/B</th>
                  <th onClick={() => toggle('avgRoe')}>ROE %</th>
                  <th onClick={() => toggle('avgDivYield')}>Div %</th>
                  <th onClick={() => toggle('avgValueScore')}>Value</th>
                  <th onClick={() => toggle('avgGrowthScore')}>Growth</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(sec => {
                  const color = SECTOR_COLORS[sec.sector] || '#6b7280'
                  const isSelected = selected === sec.sector
                  return (
                    <tr key={sec.sector}
                      onClick={() => setSelected(isSelected ? null : sec.sector)}
                      style={{ background: isSelected ? 'rgba(249,115,22,0.06)' : undefined }}>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                          <div style={{ width:10, height:10, borderRadius:2, background:color, flexShrink:0 }} />
                          <span style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                            fontSize:13, color:'var(--text)' }}>{sec.sector}</span>
                        </div>
                      </td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{sec.count}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text2)' }}>{sec.totalMktCap.toFixed(0)}</span></td>
                      {[sec.avgChange1d, sec.avgMom1w, sec.avgMom1m, sec.avgMom6m, sec.avgMom12m].map((v, i) => (
                        <td key={i}>
                          <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                            color: v != null ? (v >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text4)' }}>
                            {fp(v)}
                          </span>
                        </td>
                      ))}
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{fv(sec.avgPeFwd)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{fv(sec.avgPb, 2)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: (sec.avgRoe||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>{fp(sec.avgRoe)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: 'var(--green)' }}>{fp(sec.avgDivYield)}</span></td>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                          <div style={{ width:40, height:5, background:'var(--border)', borderRadius:2, overflow:'hidden' }}>
                            <div style={{ height:'100%', width:`${Math.min(sec.avgValueScore||0,100)}%`,
                              background:(sec.avgValueScore||0)>=60?'var(--green)':'var(--orange)' }} />
                          </div>
                          <span style={{ fontFamily:'IBM Plex Mono', fontSize:11,
                            color:(sec.avgValueScore||0)>=60?'var(--green)':'var(--orange)', fontWeight:600 }}>
                            {sec.avgValueScore != null ? Math.round(sec.avgValueScore) : 'NA'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                          <div style={{ width:40, height:5, background:'var(--border)', borderRadius:2, overflow:'hidden' }}>
                            <div style={{ height:'100%', width:`${Math.min(sec.avgGrowthScore||0,100)}%`,
                              background:(sec.avgGrowthScore||0)>=60?'var(--green)':'var(--orange)' }} />
                          </div>
                          <span style={{ fontFamily:'IBM Plex Mono', fontSize:11,
                            color:(sec.avgGrowthScore||0)>=60?'var(--green)':'var(--orange)', fontWeight:600 }}>
                            {sec.avgGrowthScore != null ? Math.round(sec.avgGrowthScore) : 'NA'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ marginTop:16, fontSize:10, color:'var(--text4)', textAlign:'center',
          borderTop:'1px solid var(--border)', paddingTop:12 }}>
          ⚠️ Data for informational purposes only · Andrea Meschini · Verona, Italy · © 2026
        </div>
      </div>
    </div>
  )
}
