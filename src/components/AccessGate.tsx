'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { supabase } from '@/lib/supabase'

/**
 * Blocco di accesso — 5/9/2026.
 *
 * ForwardAlpha torna a essere a uso personale. Chi non ha effettuato
 * l'accesso puo' vedere solo la homepage: su qualunque altra pagina
 * compare questo riquadro e il contenuto sottostante resta coperto.
 *
 * Il riquadro NON e' chiudibile di proposito: non deve esistere un modo
 * per aggirarlo cliccando fuori o premendo Esc.
 *
 * Nota: e' una protezione dell'interfaccia. La protezione vera dei dati
 * resta quella lato server, che gia' limita cosa vede un utente non
 * autenticato — questa evita che si arrivi a vedere qualcosa navigando.
 */
export default function AccessGate() {
  const pathname = usePathname()
  const [stato, setStato] = useState<'verifica' | 'dentro' | 'fuori'>('verifica')

  useEffect(() => {
    let attivo = true

    const controlla = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (attivo) setStato(session ? 'dentro' : 'fuori')
      } catch {
        if (attivo) setStato('fuori')
      }
    }
    controlla()

    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      if (attivo) setStato(session ? 'dentro' : 'fuori')
    })
    return () => { attivo = false; sub?.subscription?.unsubscribe() }
  }, [])

  // Restano accessibili la homepage (pagina di benvenuto, unica indicizzata
  // su Google), la pagina About e quella legale: i termini d'uso e
  // l'informativa privacy devono essere consultabili anche da chi non ha
  // l'accesso, come richiesto dal GDPR.
  // Tutto il resto — screener, schede titolo, settori, notizie, research,
  // about e legal — e' coperto. Nessun dato deve essere visibile a chi non
  // ha l'accesso: nemmeno la capitalizzazione o i multipli, da cui ci si
  // potrebbe fare un'idea del contenuto.
  const pagineAperte = ['/', '/about', '/legal']
  if (pagineAperte.includes(pathname || '/')) return null

  // Durante la verifica non si mostra nulla, per evitare che il riquadro
  // lampeggi a chi e' gia' autenticato.
  if (stato !== 'fuori') return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
        background: 'rgba(8,12,20,0.94)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
      }}
    >
      <div style={{
        maxWidth: 460, width: '100%', textAlign: 'center',
        border: '1px solid #243550', borderRadius: 8,
        background: '#0d1420', padding: '34px 30px',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}>
        <div style={{
          fontFamily: 'IBM Plex Sans Condensed, sans-serif',
          fontSize: 20, fontWeight: 700, letterSpacing: '0.02em',
          color: '#e8eef7', marginBottom: 18,
        }}>
          FORWARD<span style={{ color: '#94a3b8' }}>ALPHA</span>
        </div>

        <p style={{ fontSize: 15, lineHeight: 1.6, color: '#cbd5e1', margin: '0 0 14px' }}>
          ForwardAlpha is only for personal use.
        </p>

        <p style={{ fontSize: 14, lineHeight: 1.6, color: '#94a3b8', margin: 0 }}>
          If you have any interest in the product, please contact{' '}
          <a
            href="mailto:andrea@forwardalpha.pro"
            style={{ color: '#f97316', textDecoration: 'none', fontWeight: 600 }}
          >
            andrea@forwardalpha.pro
          </a>
        </p>

        <div style={{ marginTop: 26, paddingTop: 18, borderTop: '1px solid #1e2d45' }}>
          <a
            href="/"
            style={{
              display: 'inline-block',
              fontFamily: 'IBM Plex Sans Condensed, sans-serif',
              fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
              color: '#94a3b8', textDecoration: 'none',
              border: '1px solid #243550', borderRadius: 3,
              padding: '8px 18px',
            }}
          >
            BACK TO HOME
          </a>
        </div>
      </div>
    </div>
  )
}
