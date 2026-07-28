export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

// Innesca daily_eu_yahoo.yml e daily_us_yahoo.yml insieme alle 02:30
// italiane — ampiamente dopo la chiusura di entrambi i mercati (Europa
// verso le 17:30-18:00, USA in tarda serata italiana), margine di
// sicurezza sufficiente per evitare dati parziali da Yahoo Finance.

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''
const REPO = 'mesk72/euroequity-pro'
const WORKFLOWS = ['daily_eu_yahoo.yml', 'daily_us_yahoo.yml']

export async function GET(req: NextRequest) {
  if (!GITHUB_TOKEN) {
    return NextResponse.json({ error: 'GITHUB_TOKEN non configurato su Vercel' }, { status: 500 })
  }
  const results: any[] = []
  for (const workflow of WORKFLOWS) {
    try {
      const r = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`,
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
      results.push({ workflow, triggered: r.status === 204, status: r.status })
    } catch (err: any) {
      results.push({ workflow, triggered: false, error: String(err) })
    }
  }
  const allOk = results.every(r => r.triggered)
  return NextResponse.json({ triggered: allOk, results, timestamp: new Date().toISOString() }, { status: allOk ? 200 : 500 })
}
