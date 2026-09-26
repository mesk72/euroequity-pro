'use client'

import Link from 'next/link'

/**
 * Pagina Help — 26/9/2026.
 *
 * Pagina di contatto essenziale. Accessibile senza autenticazione (vedi
 * AccessGate): chi arriva sul sito e non ha accesso deve poter capire a
 * chi scrivere, senza trovarsi davanti solo un blocco.
 */
export default function HelpPage() {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg, #080c14)',
      color: 'var(--text, #e8eef7)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
    }}>
      <div style={{ maxWidth: 520, width: '100%', textAlign: 'center' }}>

        <Link href="/" style={{ textDecoration: 'none' }}>
          <div style={{
            fontFamily: 'IBM Plex Sans Condensed, sans-serif',
            fontSize: 22, fontWeight: 700, letterSpacing: '0.02em',
            color: '#e8eef7', marginBottom: 40,
          }}>
            FORWARD<span style={{ color: '#94a3b8' }}>ALPHA</span>
          </div>
        </Link>

        <h1 style={{
          fontFamily: 'IBM Plex Sans Condensed, sans-serif',
          fontSize: 13, fontWeight: 700, letterSpacing: '0.12em',
          color: '#94a3b8', margin: '0 0 28px', textTransform: 'uppercase',
        }}>
          Help
        </h1>

        <p style={{ fontSize: 17, lineHeight: 1.7, color: '#cbd5e1', margin: '0 0 8px' }}>
          Whatever you need, write me at
        </p>

        <p style={{ margin: '0 0 40px' }}>
          <a
            href="mailto:andrea@forwardalpha.pro"
            style={{
              fontSize: 18, fontWeight: 700, color: '#f97316',
              textDecoration: 'none', wordBreak: 'break-word',
            }}
          >
            andrea@forwardalpha.pro
          </a>
        </p>

        <div style={{ paddingTop: 24, borderTop: '1px solid #1e2d45' }}>
          <Link
            href="/"
            style={{
              display: 'inline-block',
              fontFamily: 'IBM Plex Sans Condensed, sans-serif',
              fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
              color: '#94a3b8', textDecoration: 'none',
              border: '1px solid #243550', borderRadius: 3,
              padding: '9px 20px',
            }}
          >
            BACK TO HOME
          </Link>
        </div>

      </div>
    </div>
  )
}
