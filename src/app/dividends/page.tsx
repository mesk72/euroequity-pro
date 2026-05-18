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
function fv(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return 'NA'
  return (v as number).toFixed(d)
}

function YieldBar({ value }: { value: number | null }) {
  if (!value) return null
  const w = Math.min(value * 8, 100) // scala: 12% yield = 100%
  const color = value >= 6 ? 'var(--green)' : value >= 3 ? 'var(--gold)' : 'var(--orange)'
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div style={{ width:60, height:8, background:'var(--border)', borderRadius:4, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${w}%`, background:color, borderRadius:4 }} />
      </div>
      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:13, color }}>
        {value.toFixed(2)}%
      </span>
    </div>
  )
}

export default function DividendsPage() {
  const router = useRouter()
  const [sectorFilter, setSectorFilter] = useState('All')
  const [minYield, setMinYield] = useState(0)
  const [n, setN] = useState(30)

  const allStocks = useMemo(() => computeScores([...DEMO_STOCKS]), [])

  const withDiv = useMemo(() =>
    allStocks
      .filter(s => s.divYield != null && s.divYield > 0)
      .filter(s => sectorFilter === 'All' || s.sector === sectorFilter)
      .filter(s => (s.divYield || 0) >= minYield)
      .sort((a, b) => (b.divYield || 0) - (a.divYield || 0))
      .slice(0, n)
  , [allStocks, sectorFilter, minYield, n])

  const sectors = ['All', ...Array.from(new Set(
    allStocks.filter(s => s.divYield && s.divYield > 0).map(s => s.sector || 'Other')
  )).sort()]

  // Stats
  const allDiv = allStocks.filter(s => s.divYield != null && s.divYield > 0)
  const avgYield  = allDiv.reduce((a, s) => a + (s.divYield || 0), 0) / (allDiv.length || 1)
  const highYield = allDiv.filter(s => (s.divYield || 0) >= 5).length
  const maxYield  = Math.max(...allDiv.map(s => s.divYield || 0))

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
          padding:8px 12px; text-align:left; border-bottom:2px solid var(--border); white-space:nowrap; }
        td { padding:8px 12px; border-bottom:1px solid rgba(30,45,69,0.5); vertical-align:middle; }
        tr:hover td { background:rgba(249,115,22,0.04); cursor:pointer; }
        input[type=range] { accent-color:var(--orange); }
        select { background:var(--bg2); border:1px solid var(--border); color:var(--text);
          padding:5px 8px; border-radius:3px; font-size:12px; font-family:'IBM Plex Sans',sans-serif; }
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

      <div style={{ maxWidth:1100, margin:'0 auto', padding:'24px 16px' }}>

        {/* Header */}
        <div style={{ marginBottom:20 }}>
          <h1 style={{ margin:'0 0 6px', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:28 }}>
            💰 Dividend Stocks — Eurozone
          </h1>
          <div style={{ fontSize:13, color:'var(--text3)' }}>
            Top dividend-paying stocks across all Eurozone markets · {allDiv.length} stocks paying dividends
          </div>
        </div>

        {/* KPIs */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:20 }}>
          {[
            { label:'Stocks paying dividends', value: allDiv.length.toString(),       color:'var(--orange)' },
            { label:'Average Dividend Yield',  value: `${avgYield.toFixed(2)}%`,     color:'var(--gold)'   },
            { label:'High Yield (≥5%)',         value: highYield.toString(),           color:'var(--green)'  },
            { label:'Highest Yield',            value: `${maxYield.toFixed(2)}%`,     color:'var(--green)'  },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:4, padding:'10px 14px', position:'relative', overflow:'hidden' }}>
              <div style={{ position:'absolute', top:0, left:0, right:0, height:2,
                background:`linear-gradient(90deg, ${color}, transparent)` }} />
              <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--text4)', marginBottom:4 }}>
                {label}
              </div>
              <div style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:22, color }}>
                {value}
              </div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div style={{ background:'var(--surface2)', border:'1px solid var(--border)',
          borderRadius:4, padding:'12px 16px', marginBottom:16,
          display:'flex', alignItems:'center', gap:20, flexWrap:'wrap' }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ fontSize:11, color:'var(--text4)', fontFamily:'IBM Plex Sans Condensed',
              fontWeight:700, textTransform:'uppercase', letterSpacing:'0.1em' }}>Sector:</span>
            <select value={sectorFilter} onChange={e => setSectorFilter(e.target.value)}>
              {sectors.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ fontSize:11, color:'var(--text4)', fontFamily:'IBM Plex Sans Condensed',
              fontWeight:700, textTransform:'uppercase', letterSpacing:'0.1em' }}>
              Min Yield: {minYield.toFixed(1)}%
            </span>
            <input type="range" min={0} max={8} step={0.5} value={minYield}
              onChange={e => setMinYield(+e.target.value)} style={{ width:100 }} />
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:6, marginLeft:'auto' }}>
            <span style={{ fontSize:11, color:'var(--text4)' }}>Show:</span>
            {[20,30,50].map(num => (
              <button key={num} onClick={() => setN(num)}
                style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:11,
                  padding:'4px 10px', borderRadius:2, cursor:'pointer',
                  border:`1px solid ${n===num?'var(--orange)':'var(--border)'}`,
                  background: n===num?'rgba(249,115,22,0.15)':'transparent',
                  color: n===num?'var(--orange)':'var(--text4)' }}>
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Yield distribution chart */}
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, padding:16, marginBottom:16 }}>
          <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
            letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)', marginBottom:12 }}>
            Dividend Yield Distribution
          </div>
          <div style={{ display:'flex', alignItems:'flex-end', gap:4, height:60 }}>
            {[0,1,2,3,4,5,6,7,8,9].map(bracket => {
              const count = allDiv.filter(s => (s.divYield||0) >= bracket && (s.divYield||0) < bracket+1).length
              const maxCount = 15
              const h = Math.max(4, (count / maxCount) * 60)
              const color = bracket >= 6 ? 'var(--green)' : bracket >= 3 ? 'var(--gold)' : 'var(--orange)'
              return (
                <div key={bracket} style={{ display:'flex', flexDirection:'column', alignItems:'center', flex:1 }}>
                  <div style={{ fontSize:9, fontFamily:'IBM Plex Mono', color:'var(--text4)', marginBottom:4 }}>
                    {count}
                  </div>
                  <div style={{ width:'100%', height:h, background:color, borderRadius:'2px 2px 0 0',
                    opacity: bracket >= minYield ? 1 : 0.3 }} />
                  <div style={{ fontSize:8, color:'var(--text4)', marginTop:3, fontFamily:'IBM Plex Mono' }}>
                    {bracket}%
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Main table */}
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, overflow:'hidden' }}>
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr>
                  <th style={{ width:40 }}>#</th>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Sector</th>
                  <th>Country</th>
                  <th>Price €</th>
                  <th>Dividend Yield</th>
                  <th>P/E Fwd</th>
                  <th>Payout %</th>
                  <th>ROE %</th>
                  <th>Mom 12M</th>
                  <th>Value Score</th>
                </tr>
              </thead>
              <tbody>
                {withDiv.map((s, i) => (
                  <tr key={`${s.ticker}.${s.exchange}`}
                    onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:12,
                        color: i === 0 ? 'var(--gold)' : 'var(--text4)' }}>
                        {i < 3 ? ['🥇','🥈','🥉'][i] : `${i+1}`}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                        color:'var(--orange)', fontSize:14 }}>
                        {s.flag} {s.ticker}
                      </span>
                    </td>
                    <td><span style={{ color:'var(--text2)', fontSize:12 }}>{s.company}</span></td>
                    <td>
                      <span style={{ fontSize:11, padding:'2px 7px', borderRadius:2,
                        background:`${SECTOR_COLORS[s.sector||'Other']||'#6b7280'}20`,
                        color: SECTOR_COLORS[s.sector||'Other']||'#9ca3af',
                        fontFamily:'IBM Plex Sans Condensed', fontWeight:600 }}>
                        {s.sector || '—'}
                      </span>
                    </td>
                    <td><span style={{ color:'var(--text3)', fontSize:12 }}>{s.country}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono' }}>{fv(s.price, 2)}</span></td>
                    <td><YieldBar value={s.divYield} /></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{fv(s.peFwd, 1)}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>NA</span></td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color:(s.roe||0)>=0?'var(--green)':'var(--red)' }}>
                        {fp(s.roe)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color:(s.mom12m||0)>=0?'var(--green)':'var(--red)' }}>
                        {fp(s.mom12m)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        fontSize:13, padding:'1px 8px', borderRadius:2,
                        background:(s.valueScore||0)>=70?'rgba(34,197,94,0.12)':'rgba(249,115,22,0.1)',
                        color:(s.valueScore||0)>=70?'var(--green)':'var(--orange)' }}>
                        {s.valueScore != null ? Math.round(s.valueScore) : 'NA'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ marginTop:16, fontSize:10, color:'var(--text4)', textAlign:'center',
          borderTop:'1px solid var(--border)', paddingTop:12 }}>
          ⚠️ Dividend yields are trailing and based on last declared dividend · Not investment advice ·
          Andrea Meschini · Verona, Italy · © 2026
        </div>
      </div>
    </div>
  )
}
