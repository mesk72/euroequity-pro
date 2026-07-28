export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

// Innesca daily_apac_yahoo.yml alle 18:00 italiane — ampiamente dopo la
// chiusura di tutti i mercati APAC (Tokyo/Hong Kong/Sydney chiudono nel
// primo pomeriggio italiano), margine di sicurezza sufficiente per
// evitare dati parziali da Yahoo Finance.

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''
const REPO = 'mesk72/euroequity-pro'
const WORKFLOW = 'daily_apac_yahoo.yml'

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
