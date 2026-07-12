import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Global Equity Research | ForwardAlpha',
  description: 'Institutional-grade quantitative equity research on 8,500+ stocks across North America, Europe, and Asia-Pacific.',
}

const MONTHS = [
  {
    month: 'June 2026',
    sectors: [
      {
        name: 'Financials',
        color: '#22c55e',
        notes: [
          {
            slug: 'BNP-PA',
            ticker: 'BNP', exchange: 'PA', company: 'BNP Paribas S.A.',
            title: 'Value 90 & Growth 80: The Institutional Mispricing of BNP Paribas',
            summary: 'Value 90, Growth 80, Best 97. NTM P/E 7.8x, P/B 0.78x, dividend 6.6%.',
            valueScore: 90, growthScore: 80, bestScore: 97,
            pdfFile: 'BNP_ForwardAlpha.pdf', date: '2026-06-03',
          }
        ]
      },
      {
        name: 'Energy',
        color: '#f97316',
        notes: [
          {
            slug: 'SHEL-LSE',
            ticker: 'SHEL', exchange: 'LSE', company: 'Shell plc',
            title: 'Value 75 & Growth 92: The Rare GARP Engine Hidden in Big Oil',
            summary: 'Value 75, Growth 92, Best 96. NTM P/E 7.9x, dividend 3.7%, EPS +24%.',
            valueScore: 75, growthScore: 92, bestScore: 96,
            pdfFile: 'SHEL_ForwardAlpha.pdf', date: '2026-06-03',
          }
        ]
      },
      {
        name: 'Industrials',
        color: '#3b82f6',
        notes: [
          {
            slug: 'ENR-XETRA',
            ticker: 'ENR', exchange: 'XETRA', company: 'Siemens Energy AG',
            title: 'Growth Score 98/100: Is Siemens Energy the Ultimate AI Infrastructure Winner?',
            summary: 'Growth 98, Value 4, Best 53. Net income +160% YoY, FCF margin 16%, net cash.',
            valueScore: 4, growthScore: 98, bestScore: 53,
            pdfFile: 'ENR_ForwardAlpha.pdf', date: '2026-06-03',
          },
          {
            slug: 'ABBN-SWX',
            ticker: 'ABBN', exchange: 'SWX', company: 'ABB Ltd',
            title: 'Growth Score 97/100: Why the Market is Paying a Premium for ABB',
            summary: 'Growth 97, Value 6, Best 56. ROIC 25%, EPS +14%, +80% 12M return.',
            valueScore: 6, growthScore: 97, bestScore: 56,
            pdfFile: 'ABBN_ForwardAlpha.pdf', date: '2026-06-03',
          }
        ]
      },
      {
        name: 'Information Technology',
        color: '#8b5cf6',
        notes: [
          {
            slug: 'ASML-AS',
            ticker: 'ASML', exchange: 'AS', company: 'ASML Holding N.V.',
            title: "Growth Score 98/100: Decoding ASML's Monopoly Power",
            summary: 'Growth 98, Value 2, Best 51. Revenue +20% YoY, EPS +29%, ROE 50%+.',
            valueScore: 2, growthScore: 98, bestScore: 51,
            pdfFile: 'ASML_ForwardAlpha.pdf', date: '2026-06-03',
          },
          {
            slug: 'IFX-XETRA',
            ticker: 'IFX', exchange: 'XETRA', company: 'Infineon Technologies AG',
            title: 'Growth Rank 99: Why IFX is a True Growth Story',
            summary: 'Growth 99, Value 5, Best 56. EPS +36%, +160% 12M return, SiC leader.',
            valueScore: 5, growthScore: 99, bestScore: 56,
            pdfFile: 'IFX_ForwardAlpha.pdf', date: '2026-06-03',
          }
        ]
      }
    ]
  }
]

export default function ResearchHubPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#0d1117', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 20px' }}>

        <div style={{ borderBottom: '2px solid #f97316', paddingBottom: 20, marginBottom: 32 }}>
          <Link href="/" style={{ color: '#f97316', fontSize: 13, textDecoration: 'none' }}>
            ← Back to Screener
          </Link>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 16, marginBottom: 8 }}>
            Research Hub
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>
            Institutional-grade quantitative equity research on 8,500+ stocks across North America, Europe, and Asia-Pacific.
          </p>
        </div>

        {MONTHS.map((monthGroup: any) => (
          <div key={monthGroup.month} style={{ marginBottom: 48 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
              <span style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9' }}>{monthGroup.month}</span>
              <div style={{ height: 1, flex: 1, background: '#1e293b' }} />
            </div>

            {monthGroup.sectors.map((sector: any) => (
              <div key={sector.name} style={{ marginBottom: 28 }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: sector.color, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ display: 'inline-block', width: 3, height: 14, background: sector.color, borderRadius: 2 }} />
                  {sector.name}
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
                  {sector.notes.map((note: any) => (
                    <Link key={note.slug} href={`/research/${note.slug}`} style={{ textDecoration: 'none' }}>
                      <div style={{ background: '#0f1923', border: '1px solid #1e293b', borderRadius: 8, padding: '14px 16px', cursor: 'pointer' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                          <span style={{ fontWeight: 800, color: '#f97316', fontSize: 13 }}>{note.ticker}</span>
                          <span style={{ color: '#64748b', fontSize: 11 }}>{note.exchange}</span>
                        </div>
                        <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>{note.company}</div>
                        <div style={{ fontSize: 11, color: '#f1f5f9', marginBottom: 10, lineHeight: 1.4 }}>{note.title}</div>
                        <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                          <div style={{ flex: 1, background: '#1e293b', borderRadius: 4, padding: '3px 6px', textAlign: 'center' }}>
                            <div style={{ fontSize: 8, color: '#93c5fd' }}>VALUE</div>
                            <div style={{ fontSize: 13, fontWeight: 800, color: '#3b82f6' }}>{note.valueScore}</div>
                          </div>
                          <div style={{ flex: 1, background: '#1e293b', borderRadius: 4, padding: '3px 6px', textAlign: 'center' }}>
                            <div style={{ fontSize: 8, color: '#86efac' }}>GROWTH</div>
                            <div style={{ fontSize: 13, fontWeight: 800, color: '#22c55e' }}>{note.growthScore}</div>
                          </div>
                          <div style={{ flex: 1, background: '#1e293b', borderRadius: 4, padding: '3px 6px', textAlign: 'center' }}>
                            <div style={{ fontSize: 8, color: '#fdba74' }}>BEST</div>
                            <div style={{ fontSize: 13, fontWeight: 800, color: '#f97316' }}>{note.bestScore}</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Link href={`/stock/${note.ticker}-${note.exchange}`}
                            style={{ flex: 1, fontSize: 10, fontWeight: 700, color: '#94a3b8',
                              background: '#1e293b', padding: '4px 6px', borderRadius: 3,
                              textDecoration: 'none', textAlign: 'center', border: '1px solid #334155' }}>
                            📊 Chart
                          </Link>
                          {note.pdfFile && (
                            <a href={`/research/${note.pdfFile}`} target="_blank" rel="noopener noreferrer"
                              style={{ flex: 1, fontSize: 10, fontWeight: 700, color: '#f97316',
                                background: '#1e293b', padding: '4px 6px', borderRadius: 3,
                                textDecoration: 'none', textAlign: 'center', border: '1px solid #f97316' }}>
                              📄 PDF
                            </a>
                          )}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}

        <div style={{ background: '#0f1923', border: '1px solid #f9731633', borderRadius: 8, padding: '24px', textAlign: 'center', marginTop: 32 }}>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>Access the Full Global Universe</div>
          <p style={{ fontSize: 13, color: '#cbd5e1', marginBottom: 16 }}>
            Screen 8,500+ equities across North America, Europe, and Asia-Pacific by Value Score, Growth Score, PE, momentum and more.
          </p>
          <Link href="/" style={{ display: 'inline-block', background: '#f97316', color: '#000', padding: '12px 28px', borderRadius: 6, fontWeight: 700, fontSize: 14, textDecoration: 'none' }}>
            Open ForwardAlpha Screener →
          </Link>
        </div>

      </div>
    </div>
  )
}
