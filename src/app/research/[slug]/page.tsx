import { Metadata } from 'next'
import Link from 'next/link'

const NOTES: Record<string, any> = {
  'BNP-PA': {
    ticker: 'BNP', exchange: 'PA', company: 'BNP Paribas S.A.',
    title: 'Value 90 & Growth 80: The Institutional Mispricing of BNP Paribas',
    summary: 'BNP scores Value 90 and Growth 80. Trading at 7.8x NTM P/E and 0.78x P/B with 6.6% dividend yield and +14% dividend growth YoY.',
    valueScore: 90, growthScore: 80, bestScore: 97,
    pdfFile: 'BNP_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Financials',
    content: `BNP Paribas S.A. (BNP) has been flagged with Value Score 90/100 and Growth Score 80/100 by ForwardAlpha.

The Valuation Disconnect
Compressed Multiples: Trading at a dirt-cheap NTM P/E of just ~7.8x, well below historical sector averages.
Massive Margin of Safety: At a Price-to-Book of ~0.78x, investors acquire BNP's franchise at a 22% discount to book value.

A High-Velocity Capital Return Engine
Stellar Yield: 6.6% dividend yield, at the very top tier of European large-cap banking.
Dividend Growth: +14% YoY dividend per share growth, signaling immense corporate confidence.

Defending Against the Value Trap
Return Expansion: LTM ROE at 9.6%, projected to expand toward 10.7%.
Intrinsic Growth: Book value per share compounding at +6.5% YoY, forward EPS scaling at ~7.6% annually.

The Quantitative Verdict
Value Rank 90/100 confirms BNP as a top-conviction name for institutional mandates seeking high-yielding, discounted quality.`
  },
  'SHEL-LSE': {
    ticker: 'SHEL', exchange: 'LSE', company: 'Shell plc',
    title: 'Value 75 & Growth 92: The Rare GARP Engine Hidden in Big Oil',
    summary: 'Shell triggers a rare dual signal: Growth Score 92 and Value Score 75. NTM P/E 7.9x with +30% 12M return and projected EPS growth of 24% per year.',
    valueScore: 75, growthScore: 92, bestScore: 96,
    pdfFile: 'SHEL_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Energy',
    content: `Shell plc (SHEL) has triggered a high-conviction dual signal: Growth Score 92/100 and Value Score 75/100.

The Earnings & Margin Inflection
Top-Line Turnaround: Double-digit revenue expansion projected for full year 2026.
Operating Leverage: Core EBITDA projected to grow +31% YoY, EBITDA margins toward 22%.
EPS Velocity: Average annual EPS growth of ~24% over the next two years.

Elite Capital Efficiency
Price Momentum: +30% 12-month price return.
FCF Engine: FCF +22% YoY, FCF margin ~9.5%.
Returns: LTM ROIC 11.7%, ROE expanding to 16.8%. Net Debt/EBITDA improving to 0.58x.

The Quantitative Verdict
NTM P/E of ~7.9x with 3.7% dividend yield. Shell represents a premier GARP opportunity for institutional portfolios.`
  },
  'ENR-XETRA': {
    ticker: 'ENR', exchange: 'XETRA', company: 'Siemens Energy AG',
    title: 'Growth Score 98/100: Is Siemens Energy the Ultimate AI Infrastructure Winner?',
    summary: 'Siemens Energy scores Growth 98/100. Net income +160% YoY, FCF margin 16%, EPS growth 93% annually. Net cash position with ROIC 17.8%.',
    valueScore: 4, growthScore: 98, bestScore: 53,
    pdfFile: 'ENR_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Industrials',
    content: `Siemens Energy AG (ENR) has been flagged with an elite Growth Score of 98/100 by ForwardAlpha.

The AI Data Center & Grid Supercycle
Unprecedented Backlog: Massive AI data center power infrastructure spending feeding directly into order books.
Indispensable Baseload: Next-generation gas turbine services bridging renewable grid stability.

Hyper-Growth Financial Inflection
Bottom-Line Scaling: Normalized net income projected to expand +160% YoY, net margins ~8.5%.
Massive Cash Generation: FCF +70% YoY, FCF margin ~16%.
Compounding Earnings: Forward EPS growing at ~93% annualized over the next two years.

Quality & Net Cash Fortress
Elite Returns: LTM ROE 23.3%, LTM ROIC 17.8%.
Zero Leverage Risk: Net Debt/EBITDA at -1.94x (net cash position).

The Quantitative Verdict
Trading at ~32x NTM P/E, when forward earnings compound at 93% the valuation multiple compresses faster than the stock rises.`
  },
  'ABBN-SWX': {
    ticker: 'ABBN', exchange: 'SWX', company: 'ABB Ltd',
    title: 'Growth Score 97/100: Why the Market is Paying a Premium for ABB',
    summary: 'ABB scores Growth 97/100 with +80% 12M return. EPS growth ~14% annually, ROIC 25%, Net Debt/EBITDA below 0.5x. Trading at 32x NTM P/E.',
    valueScore: 6, growthScore: 97, bestScore: 56,
    pdfFile: 'ABBN_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Industrials',
    content: `ABB Ltd (ABBN) has been flagged with an elite Growth Score of 97/100 by ForwardAlpha.

Structural Growth Inflection
Top-Line Velocity: Revenue growth of 10-11% annually, 2026 expansion hitting double digits.
Operating Leverage: EBITDA growth exceeding +19% YoY, margins toward 22%.
Earnings Power: Average normalized EPS growth of ~14% over the next two years.

Elite Capital Efficiency
Return on Equity: LTM ROE 33.6%, expanding to 34.5% by fiscal year-end.
Return on Invested Capital: LTM ROIC of nearly 25%.
Fortress Balance Sheet: Net Debt/EBITDA below 0.5x.

The Quantitative Verdict
Trading at ~32x NTM P/E. For quality growth mandates this premium is justified by global grid modernization and factory automation super-cycles.`
  },
  'ASML-AS': {
    ticker: 'ASML', exchange: 'AS', company: 'ASML Holding N.V.',
    title: "Growth Score 98/100: Decoding ASML's Monopoly Power",
    summary: 'ASML scores Growth 98/100. Revenue +20% YoY, EBIT margins above 36%, EPS growth ~29% annually. Net cash and ROE expanding to mid-50s.',
    valueScore: 2, growthScore: 98, bestScore: 51,
    pdfFile: 'ASML_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Information Technology',
    content: `ASML Holding N.V. (ASML) has been flagged with a near-perfect Growth Score of 98/100 by ForwardAlpha.

High-Velocity Top & Bottom-Line Scaling
Top-Line Acceleration: Full-year revenue projected to expand by nearly 20% YoY driven by AI infrastructure demand.
Extreme Pricing Power: EBIT margins on track to scale above 36%.
Earnings Power: Average annual EPS growth of ~29% over the next two years.

Elite Capital Efficiency
ROE Expansion: Return on Equity forecasted to jump to mid-50s for the current year.
Net Cash Fortress: Net Debt/EBITDA well below -0.6x.

The Quantitative Verdict
Trading at ~41x NTM P/E. ASML's absolute monopoly in EUV lithography provides a structural floor. A fundamental must-own for high-conviction institutional portfolios.`
  },
  'IFX-XETRA': {
    ticker: 'IFX', exchange: 'XETRA', company: 'Infineon Technologies AG',
    title: 'Growth Rank 99: Why IFX is a True Growth Story',
    summary: 'Infineon scores Growth 99/100. EPS growth ~36% annually, near-term EPS +65%. Trailing multiple compressing 60%+ on forward estimates. +160.1% 12M.',
    valueScore: 5, growthScore: 99, bestScore: 56,
    pdfFile: 'IFX_ForwardAlpha.pdf', date: '2026-06-03', sector: 'Information Technology',
    content: `Infineon Technologies AG (IFX) has been flagged with Growth Rank 99/100 by ForwardAlpha.

The Earnings Inflection
EPS Acceleration: Next two-year average EPS growth of ~36%, front-loaded with near-term EPS +65%.
Valuation Shift: Trailing multiple compressing by more than 60% on forward earnings estimates.

Structural Megatrend Leadership
SiC Power (Green Industrial): Global market leader for EV inverters, solar, and industrial motors.
Automotive Electrification: Every new BEV requires multiples of semiconductor content vs combustion vehicles.

Quality of Recovery
Safe Funding: Actively deleveraging, leverage ratios projected to drop >25% in the near term.
Price Momentum: +160.1% 12-month price return with mathematical fundamental backing.

The Quantitative Verdict
Growth Rank 99/100 within European equities. This is a profound earnings reversal driven by market leadership, not financial engineering.`
  },
}


const SECTOR_MAP: Record<string, string[]> = {
  'Financials':           ['BNP-PA'],
  'Energy':               ['SHEL-LSE'],
  'Industrials':          ['ENR-XETRA', 'ABBN-SWX'],
  'Information Technology': ['ASML-AS', 'IFX-XETRA'],
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
          <a href={`/pdf/${note.pdfFile}`} target="_blank" rel="noopener noreferrer"
            style={{ display:'inline-flex', alignItems:'center', gap:8,
              background:'#f97316', color:'#fff', fontWeight:700, fontSize:13,
              padding:'12px 24px', borderRadius:6, textDecoration:'none' }}>
            📄 Download Full Analysis PDF
          </a>
        )}

        {/* Related Research */}
        {(() => {
          const related = (SECTOR_MAP[note.sector] || []).filter((s: string) => s !== params.slug)
          if (related.length === 0) return null
          return (
            <div style={{ marginTop:40, paddingTop:24, borderTop:'1px solid #1e293b' }}>
              <div style={{ fontSize:12, fontWeight:700, color:'#64748b',
                textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:16 }}>
                Related Research — {note.sector}
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
                {related.map((s: string) => {
                  const r = NOTES[s]
                  if (!r) return null
                  return (
                    <Link key={s} href={`/research/${s}`}
                      style={{ background:'#111827', border:'1px solid #1e293b', borderRadius:6,
                        padding:'12px 16px', textDecoration:'none', display:'block' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                        <span style={{ background:'#1e293b', color:'#94a3b8', fontSize:11,
                          fontWeight:700, padding:'2px 8px', borderRadius:3 }}>{r.ticker}</span>
                        <span style={{ color:'#64748b', fontSize:11 }}>Growth {r.growthScore} · Value {r.valueScore}</span>
                      </div>
                      <div style={{ color:'#94a3b8', fontSize:13 }}>{r.title}</div>
                    </Link>
                  )
                })}
              </div>
            </div>
          )
        })()}

        {/* Footer — bottoni azione */}
        <div style={{ marginTop:48, paddingTop:24, borderTop:'1px solid #1e293b',
          display:'flex', gap:12, flexWrap:'wrap', alignItems:'center' }}>
          <Link href={`/stock/${note.ticker}-${note.exchange}`}
            style={{ display:'inline-flex', alignItems:'center', gap:8,
              background:'#1e293b', color:'#e2e8f0', fontWeight:700, fontSize:13,
              padding:'10px 20px', borderRadius:6, textDecoration:'none',
              border:'1px solid #334155' }}>
            📊 View {note.ticker} Chart & Data →
          </Link>
         
        </div>

      </div>
    </div>
  )
}
