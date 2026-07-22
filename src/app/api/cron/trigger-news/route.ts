export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

// Questo endpoint viene chiamato da Vercel Cron ogni 30 minuti (piano Pro,
// cron affidabile — a differenza dello schedule GitHub Actions nativo, che
// declassa/ritarda schedule piu' frequenti di un'ora durante i picchi di
// carico della piattaforma, comportamento documentato e verificato).
// Si limita a INNESCARE il workflow fetch_news_cache.yml su GitHub Actions
// (dove vive gia' la logica vera di scaricamento notizie, in Python) —
// non duplica quella logica qui, solo garantisce che parta davvero ogni
// 30 minuti, in modo affidabile.
//
// Richiede la variabile d'ambiente GITHUB_TOKEN su Vercel (un Personal
// Access Token con permesso "Actions: write" sul repository).

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''
const REPO = 'mesk72/euroequity-pro'
const WORKFLOW = 'fetch_news_cache.yml'

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

    if (r.status === 204) {
      return NextResponse.json({ triggered: true, timestamp: new Date().toISOString() })
    }
    const text = await r.text()
    return NextResponse.json({ triggered: false, status: r.status, detail: text }, { status: 500 })
  } catch (err: any) {
    return NextResponse.json({ triggered: false, error: String(err) }, { status: 500 })
  }
}
