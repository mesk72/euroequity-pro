import { Metadata } from 'next'
import Link from 'next/link'

const NOTES: Record<string, any> = {
  'SHEL-LSE': {
    ticker: 'SHEL',
    exchange: 'LSE',
    company: 'Shell plc',
    bestScore: 96,
    title: 'Value 75 & Growth 92: The Rare GARP Engine Hidden in Big Oil',
    summary: 'Shell triggers a rare dual signal: Growth Score 92 and Value Score 75. NTM P/E of 7.9x with +30% 12M price return and projected EPS growth of 24% per year.',
    valueScore: 75,
    growthScore: 92,
    pdfFile: 'SHEL_ForwardAlpha_Analysis.pdf',
    date: '2026-06-03',
    sector: 'Energy',
    content: `Shell plc (SHEL) has just triggered a high-conviction dual signal on ForwardAlpha's quantitative screening engine: Growth Score 92/100 and Value Score 75/100.

The Earnings & Margin Inflection
Top-Line Turnaround: Revenue growth is turning around, with expectations of major double-digit expansion for full year 2026.
Operating Leverage: Core EBITDA is projected to grow by over +31% YoY in 2026, driving EBITDA margins toward 22%.
Bottom-Line Velocity: Projected normalized EPS expansion pointing to an average annual EPS growth rate of about 24% over the next two years.

Elite Capital Efficiency & Price Momentum
Price Momentum: +30% price return over the past 12 months.
FCF Engine: Free Cash Flow expected to scale by more than +22% YoY in 2026, with FCF Margin of roughly 9.5%.
Improving Returns: LTM ROIC at 11.7%, ROE on track to expand to 16.8% by year-end.
De-risking Leverage: Net Debt/EBITDA projected to improve to 0.58x.

The Quantitative Verdict
Trading at a dirt-cheap NTM P/E of just ~7.9x, the market has not priced in this massive operational inflection. Backed by a 3.7% dividend yield and a rock-solid balance sheet, Shell represents a premier GARP opportunity.`
  },
  'ABBN-SWX': {
    ticker: 'ABBN',
    exchange: 'SWX',
    company: 'ABB Ltd',
    bestScore: 56,
    title: 'Growth Score 97/100: Why the Market is Paying a Premium for ABB',
    summary: 'ABB scores 97/100 on Growth with +80% 12M return. EPS growth ~14% annually, ROIC 25%, Net Debt/EBITDA below 0.5x. Trading at 32x NTM P/E.',
    valueScore: 6,
    growthScore: 97,
    pdfFile: 'ABBN_ForwardAlpha_Analysis.pdf',
    date: '2026-06-03',
    sector: 'Industrials',
    content: `ABB Ltd (ABBN) has been flagged with an elite Growth Score of 97/100 by ForwardAlpha's proprietary quantitative engine.

Structural Growth Inflection
Top-Line Velocity: Average revenue growth of 10-11% annually over the next two years, with 2026 expansion projected to hit double digits.
Operating Leverage: EBITDA growth for 2026 forecasted to exceed +19% YoY, pushing margins toward 22%.
Earnings Power: Average normalized EPS growth of about 14% over the next two years.

Elite Capital Efficiency
Return on Equity: LTM ROE at 33.6%, expected to expand to 34.5% by fiscal year-end.
Return on Invested Capital: LTM ROIC of nearly 25%.
Fortress Balance Sheet: Net Debt/EBITDA below 0.5x.

The Quantitative Verdict
An ultra-low Value Score of 6/100 indicates the market is fully pricing ABB's operational excellence at roughly 32x forward earnings. For quality and growth mandates, this premium is justified by global grid modernization and factory automation super-cycles.`
  }
}

type Props = { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const note = NOTES[params.slug]
  if (!note) return { title: 'Research | ForwardAlpha' }
  return {
    title: `${note.ticker} — ${note.title} | ForwardAlpha`,
    description: note.summary,
    openGraph: {
      title: `${note.ticker} — ${note.title}`,
      description: note.summary,
      url: `https://forwardalpha.pro/research/${params.slug}`,
      siteName: 'ForwardAlpha',
      type: 'article',
    },
  }
}

export default function ResearchNotePage({ params }: Props) {
  const note = NOTES[params.slug]

  if (!note) {
    return (
      <div style={{ minHeight:'100vh', background:'#0d1117', color:'#e2e8f0',
        display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'system-ui' }}>
        <div style={{ textAlign:'center' }}>
          <p style={{ color:'#94a3b8' }}>Research note not found.</p>
          <Link href="/research" style={{ color:'#f97316', textDecoration:'none' }}>← Back to Research</Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight:'100vh', background:'#0d1117', color:'#e2e8f0', fontFamily:'system-ui, sans-serif' }}>
      <div style={{ maxWidth:800, margin:'0 auto', padding:'32px 20px' }}>

        {/* Back */}
        <Link href="/research" style={{ color:'#f97316', fontSize:13, textDecoration:'none',
          display:'inline-flex', alignItems:'center', gap:6, marginBottom:32 }}>
          ← Research Hub
        </Link>

        {/* Header */}
        <div style={{ borderBottom:'2px solid #f97316', paddingBottom:24, marginBottom:32 }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:12 }}>
            <span style={{ background:'#f97316', color:'#fff', fontWeight:700,
              fontSize:12, padding:'4px 10px', borderRadius:4 }}>{note.ticker}</span>
            <span style={{ color:'#94a3b8', fontSize:12 }}>{note.exchange} · {note.sector}</span>
            <span style={{ color:'#64748b', fontSize:12, marginLeft:'auto' }}>{note.date}</span>
          </div>
          <h1 style={{ fontSize:22, fontWeight:800, lineHeight:1.3, color:'#f1f5f9', margin:'0 0 16px' }}>
            {note.title}
          </h1>
          <p style={{ color:'#94a3b8', fontSize:14, lineHeight:1.6, margin:0 }}>{note.summary}</p>
        </div>

        {/* Scores */}
        <div style={{ display:'flex', gap:16, marginBottom:32 }}>
          <div style={{ background:'#111827', border:'1px solid #1e293b', borderRadius:8,
            padding:'16px 24px', textAlign:'center', flex:1 }}>
            <div style={{ fontSize:28, fontWeight:800, color:'#22c55e', fontFamily:'IBM Plex Mono' }}>{note.valueScore}</div>
            <div style={{ fontSize:11, color:'#64748b', marginTop:4 }}>Value Score</div>
          </div>
          <div style={{ background:'#111827', border:'1px solid #1e293b', borderRadius:8,
            padding:'16px 24px', textAlign:'center', flex:1 }}>
            <div style={{ fontSize:28, fontWeight:800, color:'#f97316', fontFamily:'IBM Plex Mono' }}>{note.growthScore}</div>
            <div style={{ fontSize:11, color:'#64748b', marginTop:4 }}>Growth Score</div>
          </div>
          <div style={{ background:'#111827', border:'1px solid #1e293b', borderRadius:8,
            padding:'16px 24px', textAlign:'center', flex:1 }}>
            <div style={{ fontSize:28, fontWeight:800, color:'#3b82f6', fontFamily:'IBM Plex Mono' }}>
              {note.bestScore || Math.round((note.valueScore + note.growthScore) / 2)}
            </div>
            <div style={{ fontSize:11, color:'#64748b', marginTop:4 }}>Best Score</div>
          </div>
        </div>

        {/* Content */}
        <div style={{ background:'#111827', border:'1px solid #1e293b', borderRadius:8,
          padding:24, marginBottom:24 }}>
          {note.content.split('\n\n').map((para: string, i: number) => (
            <p key={i} style={{ color: i === 0 ? '#e2e8f0' : '#94a3b8',
              fontSize:14, lineHeight:1.7, marginBottom:16 }}>{para}</p>
          ))}
        </div>

        {/* PDF Download */}
        {note.pdfFile && (
          <a href={`/research/${note.pdfFile}`} target="_blank" rel="noopener noreferrer"
            style={{ display:'inline-flex', alignItems:'center', gap:8,
              background:'#f97316', color:'#fff', fontWeight:700, fontSize:13,
              padding:'12px 24px', borderRadius:6, textDecoration:'none' }}>
            📄 Download Full Analysis PDF
          </a>
        )}

        {/* Footer */}
        <div style={{ marginTop:48, paddingTop:24, borderTop:'1px solid #1e293b' }}>
          <Link href={`/stock/${note.ticker}-${note.exchange}`}
            style={{ color:'#f97316', fontSize:13, textDecoration:'none' }}>
            View {note.ticker} on ForwardAlpha →
          </Link>
        </div>

      </div>
    </div>
  )
}
