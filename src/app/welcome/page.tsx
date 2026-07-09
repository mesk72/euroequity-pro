'use client'

export default function WelcomePage() {
  const regions = [
    {
      code: 'NA',
      name: 'North America',
      detail: 'US + Canada',
      count: '~3,400 stocks',
    },
    {
      code: 'EU',
      name: 'Europe',
      detail: '16 exchanges',
      count: '~2,100 stocks',
    },
    {
      code: 'AP',
      name: 'Asia Pacific',
      detail: 'Japan · Hong Kong · Australia · Korea · Singapore',
      count: '~2,350 stocks',
    },
    {
      code: 'GCC',
      name: 'Gulf',
      detail: 'Saudi Arabia · UAE · Qatar · Kuwait · Oman · Bahrain',
      count: 'New coverage',
    },
  ]

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh', color: 'var(--text)' }}>
      {/* Nav */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 18,
          letterSpacing: '-0.01em' }}>
          FORWARD<span style={{ color: 'var(--orange)' }}>ALPHA</span>
          <span style={{ marginLeft: 8, fontSize: 9, fontWeight: 700, color: 'var(--bg)',
            background: 'var(--orange)', padding: '2px 6px', borderRadius: 3,
            verticalAlign: 'middle', letterSpacing: '0.08em' }}>BETA</span>
        </div>
        <a href="/" style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 12,
          color: 'var(--text2)', border: '1px solid var(--border2)', padding: '8px 16px',
          borderRadius: 3, textDecoration: 'none' }}>
          Sign in
        </a>
      </div>

      {/* Hero */}
      <div style={{ maxWidth: 880, margin: '0 auto', padding: '72px 24px 48px', textAlign: 'center' }}>
        <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 10,
          letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--orange)', marginBottom: 18 }}>
          Institutional-grade equity research, built for one
        </div>
        <h1 style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 'clamp(34px, 6vw, 58px)',
          lineHeight: 1.06, letterSpacing: '-0.02em', margin: '0 0 22px' }}>
          Value and growth,<br />
          <span style={{ color: 'var(--orange)' }}>ranked across four continents.</span>
        </h1>
        <p style={{ fontSize: 16, color: 'var(--text3)', maxWidth: 560, margin: '0 auto 34px', lineHeight: 1.6 }}>
          ForwardAlpha percentile-ranks ~8,000 global stocks on valuation and growth,
          the same methodology used by institutional portfolio managers — rebuilt as a
          transparent, always-on screener.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/" style={{ background: 'var(--orange)', color: '#07101f', fontFamily: 'IBM Plex Sans Condensed',
            fontWeight: 700, fontSize: 13, padding: '13px 26px', borderRadius: 4, textDecoration: 'none' }}>
            Create free account →
          </a>
          <a href="/about" style={{ border: '1px solid var(--border2)', color: 'var(--text2)',
            fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 13, padding: '13px 26px',
            borderRadius: 4, textDecoration: 'none' }}>
            How the scoring works
          </a>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text4)', marginTop: 16 }}>
          Free during Beta · No card required
        </div>
      </div>

      {/* Regions */}
      <div style={{ maxWidth: 1040, margin: '0 auto', padding: '20px 24px 64px' }}>
        <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 10,
          letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text4)',
          textAlign: 'center', marginBottom: 22 }}>
          Four markets, one framework
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
          {regions.map(r => (
            <div key={r.code} style={{ background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '22px 20px' }}>
              <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 11,
                color: 'var(--orange)', letterSpacing: '0.08em', marginBottom: 10 }}>
                {r.code}
              </div>
              <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 17,
                marginBottom: 6 }}>
                {r.name}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text3)', lineHeight: 1.5, marginBottom: 12 }}>
                {r.detail}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text4)', fontFamily: 'IBM Plex Sans Condensed',
                fontWeight: 700 }}>
                {r.count}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* What you get */}
      <div style={{ maxWidth: 1040, margin: '0 auto', padding: '0 24px 72px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          {[
            { t: 'Value Score', d: 'PE trailing, PE forward, and Price/Book ranked against same-market peers.' },
            { t: 'Growth Score', d: 'EPS growth, revenue growth, and 6/12-month price momentum, combined.' },
            { t: 'Best Score', d: 'Value + Growth, re-ranked — the shortlist of what deserves a closer look.' },
          ].map(x => (
            <div key={x.t} style={{ borderLeft: '2px solid var(--orange)', paddingLeft: 16 }}>
              <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 14,
                marginBottom: 6 }}>{x.t}</div>
              <div style={{ fontSize: 12.5, color: 'var(--text3)', lineHeight: 1.55 }}>{x.d}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: '1px solid var(--border)', padding: '28px 24px' }}>
        <div style={{ maxWidth: 1040, margin: '0 auto', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ fontSize: 11, color: 'var(--text4)' }}>
            © {new Date().getFullYear()} ForwardAlpha · Andrea Meschini · Verona, Italy
          </div>
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <a href="/about" style={{ fontSize: 11, color: 'var(--text3)', textDecoration: 'none' }}>About</a>
            <a href="/legal" style={{ fontSize: 11, color: 'var(--text3)', textDecoration: 'none' }}>Legal</a>
            <a href="/legal" style={{ fontSize: 11, color: 'var(--text3)', textDecoration: 'none' }}>Terms of Use</a>
            <a href="mailto:andrea@forwardalpha.pro" style={{ fontSize: 11, color: 'var(--text3)', textDecoration: 'none' }}>Contact</a>
          </div>
        </div>
        <div style={{ maxWidth: 1040, margin: '10px auto 0', fontSize: 10, color: 'var(--text4)' }}>
          For informational purposes only. Not investment advice.
        </div>
      </div>
    </div>
  )
}
