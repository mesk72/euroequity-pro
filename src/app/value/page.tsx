'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, TrendingUp, Star, BarChart2 } from 'lucide-react'
import { computeScores } from '@/lib/ranking'
import { DEMO_STOCKS } from '@/lib/demoData'
import { SECTOR_COLORS } from '@/lib/constants'

function fv(v?: number | null, d = 1): string {
  if (v == null || isNaN(v as number)) return 'NA'
  return (v as number).toFixed(d)
}
function fp(v?: number | null, d = 1): string {
  if (v == null || isNaN(v as number)) return 'NA'
  return `${(v as number) >= 0 ? '+' : ''}${(v as number).toFixed(d)}%`
}
function fn(v?: number | null): string {
  if (v == null) return 'NA'
  return String(Math.round(v as number))
}

function ScoreBadge({ value }: { value: number | null }) {
  if (value == null) return <span style={{ color:'var(--text4)', fontFamily:'IBM Plex Mono' }}>NA</span>
  const v = Math.round(value)
  const color = v >= 70 ? 'var(--green)' : v >= 40 ? 'var(--orange)' : 'var(--red)'
  const bg    = v >= 70 ? 'rgba(34,197,94,0.12)' : v >= 40 ? 'rgba(249,115,22,0.1)' : 'rgba(239,68,68,0.1)'
  return (
    <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:14,
      background:bg, color, padding:'2px 10px', borderRadius:3, display:'inline-block' }}>
      {v}
    </span>
  )
}

function ScoreBar({ value, color }: { value: number | null; color: string }) {
  if (value == null) return null
  const v = Math.min(Math.max(Math.round(value), 0), 100)
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div style={{ flex:1, height:6, background:'var(--border)', borderRadius:3, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${v}%`, background:color, borderRadius:3,
          transition:'width 0.4s ease' }} />
      </div>
      <span style={{ fontFamily:'IBM Plex Mono', fontSize:11, color, fontWeight:700, width:28, textAlign:'right' }}>
        {v}
      </span>
    </div>
  )
}

type Tab = 'value' | 'growth' | 'combined' | 'dividend'

export default function ValuePage() {
  const router  = useRouter()
  const [tab,   setTab]   = useState<Tab>('value')
  const [n,     setN]     = useState(20)

  const allStocks = useMemo(() => computeScores([...DEMO_STOCKS]), [])

  const ranked = useMemo(() => {
    const sorted = [...allStocks]
    switch (tab) {
      case 'value':
        return sorted
          .filter(s => s.valueScore != null)
          .sort((a, b) => (b.valueScore || 0) - (a.valueScore || 0))
          .slice(0, n)
      case 'growth':
        return sorted
          .filter(s => s.growthScore != null)
          .sort((a, b) => (b.growthScore || 0) - (a.growthScore || 0))
          .slice(0, n)
      case 'combined':
        return sorted
          .filter(s => s.valueScore != null && s.growthScore != null)
          .sort((a, b) => {
            const scoreA = ((a.valueScore || 0) + (a.growthScore || 0)) / 2
            const scoreB = ((b.valueScore || 0) + (b.growthScore || 0)) / 2
            return scoreB - scoreA
          })
          .slice(0, n)
      case 'dividend':
        return sorted
          .filter(s => s.divYield != null && s.divYield > 0)
          .sort((a, b) => (b.divYield || 0) - (a.divYield || 0))
          .slice(0, n)
      default:
        return []
    }
  }, [allStocks, tab, n])

  // Statistiche per il tab corrente
  const stats = useMemo(() => {
    const withValue  = allStocks.filter(s => s.valueScore != null)
    const withGrowth = allStocks.filter(s => s.growthScore != null)
    const avgValue   = withValue.length ? withValue.reduce((a,s) => a+(s.valueScore||0),0)/withValue.length : 0
    const avgGrowth  = withGrowth.length ? withGrowth.reduce((a,s) => a+(s.growthScore||0),0)/withGrowth.length : 0
    const highValue  = withValue.filter(s => (s.valueScore||0) >= 70).length
    const highGrowth = withGrowth.filter(s => (s.growthScore||0) >= 70).length
    return { avgValue, avgGrowth, highValue, highGrowth, total: allStocks.length }
  }, [allStocks])

  const today = new Date().toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' })

  const TABS: { id: Tab; label: string; icon: string; desc: string }[] = [
    { id:'value',    label:'Top Value',    icon:'💎', desc:'Ranked by Value Score (P/E, P/B inverse rank)' },
    { id:'growth',   label:'Top Growth',   icon:'🚀', desc:'Ranked by Growth Score (EPS growth, revenue growth, momentum)' },
    { id:'combined', label:'Best Overall', icon:'⭐', desc:'Ranked by average of Value + Growth Score' },
    { id:'dividend', label:'Top Dividend', icon:'💰', desc:'Ranked by Dividend Yield %' },
  ]

  return (
    <div style={{ background:'var(--bg)', minHeight:'100vh', fontFamily:'IBM Plex Sans, sans-serif', fontSize:13 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&display=swap');
        :root {
          --bg:#0a0e1a; --bg2:#0d1221; --surface:#111827; --surface2:#161d2e;
          --border:#1e2d45; --border2:#243550; --orange:#f97316;
          --green:#22c55e; --red:#ef4444; --gold:#eab308;
          --text:#ffffff; --text2:#e2e8f0; --text3:#cbd5e1; --text4:#94a3b8;
        }
        body { background:var(--bg); margin:0; color:var(--text); }
        * { box-sizing:border-box; }
        table { width:100%; border-collapse:collapse; }
        th { background:var(--surface2); color:var(--text4); font-family:'IBM Plex Sans Condensed',sans-serif;
          font-size:10px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
          padding:8px 12px; text-align:left; border-bottom:2px solid var(--border); white-space:nowrap; }
        td { padding:8px 12px; border-bottom:1px solid rgba(30,45,69,0.5); vertical-align:middle; }
        tr:hover td { background:rgba(249,115,22,0.04); cursor:pointer; }
        tr:nth-child(even) td { background:rgba(17,24,39,0.4); }
        tr:nth-child(even):hover td { background:rgba(249,115,22,0.04); }
      `}</style>

      {/* Top nav */}
      <div style={{ background:'var(--surface)', borderBottom:'2px solid var(--orange)',
        padding:'0 24px', height:44, display:'flex', alignItems:'center', gap:16, flexShrink:0 }}>
        <button onClick={() => router.push('/')}
          style={{ display:'flex', alignItems:'center', gap:6, color:'var(--text4)',
            background:'none', border:'none', cursor:'pointer', fontSize:13 }}>
          <ArrowLeft size={15} /> Back to Dashboard
        </button>
        <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
          fontSize:18, color:'var(--orange)' }}>
          EURO<span style={{ color:'var(--text3)' }}>EQUITY</span> PRO
        </div>
      </div>

      <div style={{ maxWidth:1100, margin:'0 auto', padding:'24px 16px' }}>

        {/* Page header */}
        <div style={{ marginBottom:24 }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:8 }}>
            <Star size={24} style={{ color:'var(--orange)' }} />
            <h1 style={{ margin:0, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              fontSize:28, color:'var(--text)' }}>
              Best Opportunities — Eurozone
            </h1>
          </div>
          <div style={{ fontSize:13, color:'var(--text3)' }}>
            Quantitative ranking of {stats.total} Eurozone stocks · Updated {today}
          </div>
          <div style={{ fontSize:11, color:'var(--text4)', marginTop:4 }}>
            Rank formula: Rank(x) = (count(xi &lt; x) + 0.5 × count(xi = x)) / N × 100 · Scores calculated per national exchange
          </div>
        </div>

        {/* KPI strip */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:24 }}>
          {[
            { label:'Total Stocks', value: stats.total.toString(), color:'var(--orange)' },
            { label:'Avg Value Score', value: Math.round(stats.avgValue).toString(), color:'var(--green)' },
            { label:'Avg Growth Score', value: Math.round(stats.avgGrowth).toString(), color:'var(--gold)' },
            { label:'High Value Score (≥70)', value: stats.highValue.toString(), color:'var(--green)' },
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

        {/* Tabs */}
        <div style={{ display:'flex', gap:6, marginBottom:16, flexWrap:'wrap' }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:13,
                padding:'8px 18px', borderRadius:3, cursor:'pointer',
                border:`1px solid ${tab === t.id ? 'var(--orange)' : 'var(--border)'}`,
                background: tab === t.id ? 'var(--orange)' : 'transparent',
                color: tab === t.id ? '#fff' : 'var(--text3)',
                display:'flex', alignItems:'center', gap:6 }}>
              {t.icon} {t.label}
            </button>
          ))}
          <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ fontSize:11, color:'var(--text4)' }}>Show top:</span>
            {[10, 20, 30].map(num => (
              <button key={num} onClick={() => setN(num)}
                style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:11,
                  padding:'4px 10px', borderRadius:2, cursor:'pointer',
                  border:`1px solid ${n === num ? 'var(--orange)' : 'var(--border)'}`,
                  background: n === num ? 'rgba(249,115,22,0.15)' : 'transparent',
                  color: n === num ? 'var(--orange)' : 'var(--text4)' }}>
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Description */}
        <div style={{ fontSize:12, color:'var(--text4)', marginBottom:16,
          background:'var(--surface2)', border:'1px solid var(--border)',
          borderRadius:3, padding:'8px 14px' }}>
          {TABS.find(t => t.id === tab)?.desc}
        </div>

        {/* Table */}
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, overflow:'hidden' }}>
          <div style={{ overflowX:'auto' }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width:40 }}>#</th>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Sector</th>
                  <th>Country</th>
                  <th>Price €</th>
                  <th>P/E Fwd</th>
                  <th>P/B</th>
                  <th>ROE %</th>
                  <th>Div %</th>
                  <th>EPS Gr %</th>
                  <th>Value Score</th>
                  <th>Growth Score</th>
                </tr>
              </thead>
              <tbody>
                {ranked.map((s, i) => (
                  <tr key={`${s.ticker}.${s.exchange}`}
                    onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        color: i === 0 ? 'var(--gold)' : i === 1 ? 'var(--text3)' : i === 2 ? '#cd7f32' : 'var(--text4)',
                        fontSize: i < 3 ? 15 : 12 }}>
                        {i < 3 ? ['🥇','🥈','🥉'][i] : `${i+1}`}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                        color:'var(--orange)', fontSize:14 }}>
                        {s.flag} {s.ticker}
                      </span>
                    </td>
                    <td>
                      <span style={{ color:'var(--text2)', fontSize:12 }}>{s.company}</span>
                    </td>
                    <td>
                      <span style={{ fontSize:11, padding:'2px 8px', borderRadius:2,
                        background: `${SECTOR_COLORS[s.sector || 'Other'] || '#6b7280'}20`,
                        color: SECTOR_COLORS[s.sector || 'Other'] || '#9ca3af',
                        fontFamily:'IBM Plex Sans Condensed', fontWeight:600 }}>
                        {s.sector || '—'}
                      </span>
                    </td>
                    <td><span style={{ color:'var(--text3)', fontSize:12 }}>{s.country}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text)' }}>{fv(s.price, 2)}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{fv(s.peFwd, 1)}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text3)' }}>{fv(s.pb, 2)}</span></td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: (s.roe||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {fp(s.roe)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: (s.divYield||0) > 0 ? 'var(--green)' : 'var(--text4)' }}>
                        {fp(s.divYield)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: (s.epsGrowth||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {fp(s.epsGrowth)}
                      </span>
                    </td>
                    <td style={{ minWidth:120 }}>
                      <ScoreBar value={s.valueScore} color={
                        (s.valueScore||0) >= 70 ? 'var(--green)' :
                        (s.valueScore||0) >= 40 ? 'var(--orange)' : 'var(--red)'
                      } />
                    </td>
                    <td style={{ minWidth:120 }}>
                      <ScoreBar value={s.growthScore} color={
                        (s.growthScore||0) >= 70 ? 'var(--green)' :
                        (s.growthScore||0) >= 40 ? 'var(--orange)' : 'var(--red)'
                      } />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{ marginTop:16, fontSize:10, color:'var(--text4)',
          textAlign:'center', borderTop:'1px solid var(--border)', paddingTop:12 }}>
          ⚠️ Quantitative scores do not constitute investment advice ·
          Andrea Meschini · Verona, Italy · langskltdlondon@gmail.com · © 2026
        </div>
      </div>
    </div>
  )
}
