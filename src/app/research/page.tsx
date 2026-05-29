import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'European Equity Research | ForwardAlpha — Quantitative Analysis',
  description: 'Institutional-grade quantitative equity research on European stocks. Value Score, Growth Score and fundamental analysis on ASML, Shell, BNP Paribas, Siemens Energy, Rio Tinto and more.',
  openGraph: {
    title: 'ForwardAlpha European Equity Research',
    description: 'Quantitative research combining proprietary Value & Growth scoring models with fundamental analysis across 3,600+ European equities.',
    url: 'https://forwardalpha.pro/research',
    siteName: 'ForwardAlpha',
    type: 'website',
  },
}

const SECTORS = [
  {
    name: 'Financials & Banking',
    color: '#3b82f6',
    bg: '#eff6ff',
    notes: [
      { ticker: 'BNP', slug: 'bnp', flag: '🇫🇷', company: 'BNP Paribas S.A.', tagline: 'Deep Value & Resilient Income Engine', value: 79, growth: 64 },
      { ticker: 'INGA', slug: 'inga', flag: '🇳🇱', company: 'ING Groep N.V.', tagline: 'A Rare Blueprint for Financial Sector GARP', value: 75, growth: 60 },
      { ticker: 'UBSG', slug: 'ubsg', flag: '🇨🇭', company: 'UBS Group AG', tagline: 'Operational Leverage at Scale', value: 69, growth: 65 },
    ],
  },
  {
    name: 'Technology & Semiconductors',
    color: '#8b5cf6',
    bg: '#faf5ff',
    notes: [
      { ticker: 'ASML', slug: 'asml', flag: '🇳🇱', company: 'ASML Holding N.V.', tagline: 'The Quantitative Growth Engine — EUV Monopoly', value: 19, growth: 86 },
      { ticker: 'IFX', slug: 'ifx', flag: '🇩🇪', company: 'Infineon Technologies AG', tagline: 'Violent Multiple Compression in Tech', value: 21, growth: 86 },
    ],
  },
  {
    name: 'Energy & Infrastructure',
    color: '#f97316',
    bg: '#fff7ed',
    notes: [
      { ticker: 'SHEL', slug: 'shel', flag: '🇬🇧', company: 'Shell plc', tagline: 'High-Yielding Cash Machine & Structural Turnaround', value: 66, growth: 71 },
      { ticker: 'EQNR', slug: 'eqnr', flag: '🇳🇴', company: 'Equinor ASA', tagline: 'The Deep Value & Cash Engine', value: 59, growth: 63 },
      { ticker: 'ENR', slug: 'enr', flag: '🇩🇪', company: 'Siemens Energy AG', tagline: 'Hyper-Growth in the AI Grid Supercycle', value: 17, growth: 87 },
      { ticker: 'PRY', slug: 'pry', flag: '🇮🇹', company: 'Prysmian S.p.A.', tagline: 'Infrastructure Backlog Powering the Green Transition', value: 17, growth: 85 },
    ],
  },
  {
    name: 'Basic Materials & Industrials',
    color: '#16a34a',
    bg: '#f0fdf4',
    notes: [
      { ticker: 'RIO', slug: 'rio', flag: '🇬🇧', company: 'Rio Tinto Group', tagline: 'The Institutional Quality Blueprint', value: 46, growth: 74 },
      { ticker: 'MT', slug: 'mt', flag: '🇱🇺', company: 'ArcelorMittal S.A.', tagline: 'Growth Momentum & Asymmetric Risk-Reward', value: 71, growth: 81 },
      { ticker: 'VOW3', slug: 'vow3', flag: '🇩🇪', company: 'Volkswagen AG', tagline: 'The Ultimate Value Paradox', value: 96, growth: 43 },
    ],
  },
]

export default function ResearchHubPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg, #0d1117)', color: 'var(--text, #e2e8f0)', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 20px' }}>

        {/* Header */}
        <div style={{ borderBottom: '2px solid #f97316', paddingBottom: 20, marginBottom: 32 }}>
          <Link href="/" style={{ color: '#f97316', fontSize: 13, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 16 }}>
            ← Back to ForwardAlpha
          </Link>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#f97316', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
            ForwardAlpha · Quantitative Equity Research
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, margin: '0 0 8px' }}>European Equity Research Coverage</h1>
          <p style={{ fontSize: 14, color: '#cbd5e1', margin: 0, maxWidth: 600 }}>
            Institutional-grade quantitative analysis combining our proprietary Value &amp; Growth scoring models
            with fundamental research across the European equity universe.
          </p>
        </div>

        {/* Sectors */}
        {SECTORS.map(sector => (
          <div key={sector.name} style={{ marginBottom: 40 }}>
            <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: sector.color, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ display: 'inline-block', width: 3, height: 16, background: sector.color, borderRadius: 2 }} />
              {sector.name}
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
              {sector.notes.map(note => (
                <Link key={note.slug} href={`/research/${note.slug}`} style={{ textDecoration: 'none' }}>
                  <div style={{ background: '#0f1923', border: '1px solid #1e293b', borderRadius: 8, padding: '16px', transition: 'border-color 0.2s', cursor: 'pointer' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span style={{ fontSize: 18 }}>{note.flag}</span>
                      <span style={{ fontWeight: 800, color: '#f97316', fontSize: 14 }}>{note.ticker}</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#cbd5e1', marginBottom: 4 }}>{note.company}</div>
                    <div style={{ fontSize: 12, color: '#f1f5f9', marginBottom: 12, lineHeight: 1.4 }}>{note.tagline}</div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <div style={{ flex: 1, background: '#eff6ff', borderRadius: 4, padding: '4px 8px', textAlign: 'center' }}>
                        <div style={{ fontSize: 9, color: '#93c5fd' }}>VALUE</div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: '#3b82f6' }}>{note.value}</div>
                      </div>
                      <div style={{ flex: 1, background: '#f0fdf4', borderRadius: 4, padding: '4px 8px', textAlign: 'center' }}>
                        <div style={{ fontSize: 9, color: '#86efac' }}>GROWTH</div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: '#22c55e' }}>{note.growth}</div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}

        {/* CTA */}
        <div style={{ background: '#0f1923', border: '1px solid #f9731633', borderRadius: 8, padding: '24px', textAlign: 'center', marginTop: 16 }}>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>Access the Full European Universe</div>
          <p style={{ fontSize: 13, color: '#cbd5e1', marginBottom: 16 }}>
            Screen 3,600+ European equities by Value Score, Growth Score, PE, momentum and more.
          </p>
          <Link href="/" style={{ display: 'inline-block', background: '#f97316', color: '#000', padding: '12px 28px', borderRadius: 8, fontWeight: 800, fontSize: 13, textDecoration: 'none' }}>
            Open ForwardAlpha Screener →
          </Link>
        </div>

        {/* Disclaimer */}
        <div style={{ borderTop: '1px solid #1e293b', paddingTop: 16, marginTop: 24 }}>
          <p style={{ fontSize: 10, color: '#475569', lineHeight: 1.5, margin: 0 }}>
            <strong>DISCLAIMER.</strong> All research published on ForwardAlpha is for informational and educational purposes only.
            It does not constitute investment advice. ForwardAlpha is not a registered investment adviser.
            © 2026 ForwardAlpha · forwardalpha.pro
          </p>
        </div>

      </div>
    </div>
  )
}
