'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, ArrowLeft } from 'lucide-react'

const SECTOR_COLORS: Record<string, string> = {
  'Financials':'#3b82f6','Technology':'#8b5cf6','Health Care':'#10b981',
  'Energy':'#f59e0b','Industrials':'#6366f1','Consumer Discretionary':'#ec4899',
  'Consumer Staples':'#14b8a6','Materials':'#f97316','Utilities':'#06b6d4',
  'Communication Services':'#84cc16','Real Estate':'#a855f7','Other':'#6b7280',
}

function fp(v?:number|null,d=1):string{ if(v==null||isNaN(v))return'-'; return `${v>=0?'+':''}${v.toFixed(d)}%` }
function fv(v?:number|null,d=2):string{ if(v==null||isNaN(v))return'-'; return (v as number).toFixed(d) }
function fn(v?:number|null):string{ if(v==null||isNaN(v as number))return'-'; return String(Math.round(v as number)) }

export default function SectorsPage() {
  const [stocks,   setStocks]   = useState<any[]>([])
  const [loading,  setLoading]  = useState(true)
  const [selected, setSelected] = useState<string|null>(null)
  const [exchange, setExchange] = useState('All')

  useEffect(() => {
    setLoading(true)
    fetch('/api/db/stocks')
      .then(r => r.ok ? r.json() : { stocks: [] })
      .then(d => { setStocks(d.stocks||[]); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const exchanges = ['All', ...Array.from(new Set(stocks.map((s:any)=>s.exchange))).sort()] as string[]
  const filtered  = exchange === 'All' ? stocks : stocks.filter((s:any)=>s.exchange===exchange)

  // Aggrega per settore
  const sectorMap: Record<string, any[]> = {}
  for (const s of filtered) {
    const sec = s.sector || 'Other'
    if (!sectorMap[sec]) sectorMap[sec] = []
    sectorMap[sec].push(s)
  }

  const sectorStats = Object.entries(sectorMap).map(([sector, list]) => {
    const totalCap = list.reduce((a:number,s:any)=>a+(s.mktCap||0),0)
    const mcw = (field:string) => {
      const v = list.filter((s:any)=>s[field]!=null&&s.mktCap!=null&&s.mktCap>0)
      const tw = v.reduce((a:number,s:any)=>a+(s.mktCap||0),0)
      return tw>0 ? v.reduce((a:number,s:any)=>a+(s[field]||0)*(s.mktCap||0),0)/tw : null
    }
    const avgChg = mcw('change1d')
    const avgVal = mcw('valueScore')
    const avgGrow = mcw('growthScore')
    const avgBest = mcw('combinedRank')
    const avgPE = (() => { const v=list.filter((s:any)=>s.peTrail!=null&&s.peTrail>0&&s.mktCap!=null&&s.mktCap>0); const tw=v.reduce((a:number,s:any)=>a+(s.mktCap||0),0); return tw>0?v.reduce((a:number,s:any)=>a+(s.peTrail||0)*(s.mktCap||0),0)/tw:null })()
    return { sector, count:list.length, avgChg, totalCap, avgPE, avgVal, avgGrow, avgBest, stocks:list }
  }).sort((a,b)=>b.totalCap-a.totalCap)

  const selectedStocks = selected
    ? (sectorMap[selected]||[]).sort((a:any,b:any)=>(b.mktCap||0)-(a.mktCap||0)).slice(0,50)
    : []

  return (
    <div style={{ background:'var(--bg)',minHeight:'100vh',color:'var(--text)',
      fontFamily:'IBM Plex Sans, sans-serif',padding:24 }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');
      *{box-sizing:border-box;margin:0;padding:0}
      table{width:100%;border-collapse:collapse;font-size:12px}
      th{padding:8px 10px;text-align:left;border-bottom:1px solid #1e2840;font-size:9px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6b7280;white-space:nowrap}
      td{padding:7px 10px;border-bottom:1px solid #0f1623;white-space:nowrap}
      tr:hover td{background:rgba(255,255,255,0.03)}
      select{background:#0f1623;border:1px solid #1e2840;color:#e2e8f0;padding:6px 10px;border-radius:4px;font-size:12px;font-family:inherit}
      `}</style>

      <a href="/" style={{ display:'flex',alignItems:'center',gap:8,color:'#f97316',textDecoration:'none',fontSize:13,marginBottom:20 }}>
        <ArrowLeft size={14}/> Back
      </a>

      <div style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,fontSize:22,marginBottom:4 }}>
        🏭 Sector Analysis
      </div>
      <div style={{ fontSize:11,color:'#6b7280',marginBottom:20 }}>
        ⚠️ Prices delayed 15-20 min · Fundamentals updated daily
      </div>

      {/* Filter */}
      <div style={{ marginBottom:16,display:'flex',alignItems:'center',gap:12 }}>
        <span style={{ fontSize:11,color:'#6b7280' }}>Exchange:</span>
        <select value={exchange} onChange={e=>setExchange(e.target.value)}>
          {exchanges.map(e=><option key={e}>{e}</option>)}
        </select>
        <span style={{ fontSize:11,color:'#6b7280' }}>{filtered.length} stocks</span>
      </div>

      {loading ? (
        <div style={{ textAlign:'center',padding:60,color:'#6b7280' }}>
          <RefreshCw size={24} style={{ animation:'spin 1s linear infinite',margin:'0 auto 12px',display:'block' }}/>
          Loading sector data…
        </div>
      ) : (
        <>
          {/* Heatmap settori */}
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(160px,1fr))',gap:8,marginBottom:24 }}>
            {sectorStats.map(({sector,count,avgChg,totalCap,avgVal,avgGrow})=>{
              const color = SECTOR_COLORS[sector]||'#6b7280'
              const isSelected = selected===sector
              return (
                <div key={sector}
                  onClick={()=>setSelected(isSelected?null:sector)}
                  style={{ background:isSelected?`${color}25`:'#0d1220',
                    border:`1px solid ${isSelected?color:'#1e2840'}`,
                    borderLeft:`3px solid ${color}`,borderRadius:4,padding:'12px 14px',
                    cursor:'pointer',transition:'all 0.15s' }}>
                  <div style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,fontSize:12,
                    color,marginBottom:6,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis' }}>
                    {sector}
                  </div>
                  <div style={{ fontFamily:'IBM Plex Mono',fontSize:18,fontWeight:700,
                    color:avgChg==null?'#6b7280':avgChg>=0?'#22c55e':'#ef4444',marginBottom:4 }}>
                    {avgChg!=null?fp(avgChg):'-'}
                  </div>
                  <div style={{ fontSize:10,color:'#6b7280' }}>{count} stocks · {totalCap.toFixed(0)}B</div>
                  <div style={{ display:'flex',gap:8,marginTop:6 }}>
                    <span style={{ fontSize:10,color:(avgVal||0)>=70?'#22c55e':(avgVal||0)>=40?'#f97316':'#ef4444' }}>
                      V:{fn(avgVal)}
                    </span>
                    <span style={{ fontSize:10,color:(avgGrow||0)>=70?'#22c55e':(avgGrow||0)>=40?'#f97316':'#ef4444' }}>
                      G:{fn(avgGrow)}
                    </span>
                    <span style={{ fontSize:10,color:(avgBest||0)>=70?'#22c55e':(avgBest||0)>=40?'#f97316':'#ef4444' }}>
                     B:{fn(avgBest)}
                    }
                  </div>
                </div>
              )
            })}
          </div>

          {/* Titoli del settore selezionato */}
          {selected && (
            <div style={{ background:'#0d1220',border:'1px solid #1e2840',borderRadius:4,overflowX:'auto' }}>
              <div style={{ padding:'8px 12px',borderBottom:'1px solid #1e2840',
                fontFamily:'IBM Plex Sans Condensed',fontWeight:700,fontSize:11,
                letterSpacing:'0.1em',textTransform:'uppercase',
                color:SECTOR_COLORS[selected]||'#6b7280' }}>
                {selected} — Top 50 by Market Cap
              </div>
              <table>
                <thead><tr>
                  <th>Ticker</th><th>Company</th><th>Exchange</th>
                  <th>Price</th><th>1D %</th><th>Mkt Cap B</th>
                  <th>P/E</th><th>P/B</th><th>Value</th><th>Growth</th>
                </tr></thead>
                <tbody>
                  {selectedStocks.map((s:any,i:number)=>(
                    <tr key={i} onClick={()=>window.location.href=`/stock/${s.ticker}-${s.exchange}`}
                      style={{ cursor:'pointer' }}>
                      <td style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,color:'#f97316' }}>{s.flag} {s.ticker}</td>
                      <td style={{ color:'#94a3b8',maxWidth:160,overflow:'hidden',textOverflow:'ellipsis' }}>{s.company}</td>
                      <td style={{ fontSize:10,color:'#6b7280' }}>{s.exchange}</td>
                      <td style={{ fontFamily:'IBM Plex Mono' }}>{fv(s.price,2)}</td>
                      <td style={{ fontFamily:'IBM Plex Mono',color:(s.change1d||0)>=0?'#22c55e':'#ef4444' }}>{fp(s.change1d)}</td>
                      <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.mktCap,1)}</td>
                      <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.peTrail,1)}</td>
                      <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.pb,2)}</td>
                      <td style={{ fontFamily:'IBM Plex Mono',fontWeight:700,
                        color:(s.valueScore||0)>=70?'#22c55e':(s.valueScore||0)>=40?'#f97316':'#ef4444' }}>
                        {fn(s.valueScore)}
                      </td>
                      <td style={{ fontFamily:'IBM Plex Mono',fontWeight:700,
                        color:(s.growthScore||0)>=70?'#22c55e':(s.growthScore||0)>=40?'#f97316':'#ef4444' }}>
                        {fn(s.growthScore)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
