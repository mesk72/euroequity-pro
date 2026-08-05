export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

// Innesca daily_eu_yahoo.yml alle 21:00 italiane, subito dopo la
// chiusura dei mercati europei (17:30) e dopo che Yahoo ha pubblicato le
// chiusure definitive (circa 40 minuti dopo la campana, verificato il
// 4/8/2026). Cosi' il sito e' aggiornato la sera stessa invece che
// l'indomani. La passata notturna di trigger-daily-eu-us resta come
// recupero per i titoli pubblicati in ritardo.
//

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''
const REPO = 'mesk72/euroequity-pro'
const WORKFLOW = 'daily_eu_yahoo.yml'

export async function GET(req: NextRequest) {
  if (!GITHUB_TOKEN) {
    return NextResponse.json({ error: 'GITHUB_TOKEN non configurato su Vercel' }, { status: 500 })
  }
  try {
    const r = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
          Accept: 'application/vnd.github+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    )
    const ok = r.status === 204
    return NextResponse.json(
      { triggered: ok, status: r.status, timestamp: new Date().toISOString() },
      { status: ok ? 200 : 500 }
    )
  } catch (err: any) {
    return NextResponse.json(
      { triggered: false, error: String(err), timestamp: new Date().toISOString() },
      { status: 500 }
    )
  }
}
