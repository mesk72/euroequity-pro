export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

// Innesca daily_report.yml alle 08:00 italiane.
//
// Perche' esiste: il rapporto giornaliero aveva SOLO il cron nativo di
// GitHub, che accoda i lavori programmati. Misurato sul daily US dal 2 al
// 5 agosto 2026: ritardo sistematico di oltre 3 ore ogni giorno (partiva
// verso le 04:00 invece che alle 00:30). Il 4 agosto il rapporto non e'
// partito affatto. Gli script dei prezzi avevano gia' questa doppia
// copertura (Vercel puntuale + GitHub come riserva), il rapporto no.

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''
const REPO = 'mesk72/euroequity-pro'
const WORKFLOW = 'daily_report.yml'

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
