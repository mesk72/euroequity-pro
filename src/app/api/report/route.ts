import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const { headlines } = await req.json()
    if (!headlines || headlines.length === 0) {
      return NextResponse.json({ error: 'No headlines provided' }, { status: 400 })
    }

    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    })

    const headlinesText = headlines
      .slice(0, 25)
      .map((n: any) => `- [${n.source}] ${n.title}`)
      .join('\n')

    const prompt = `You are a senior financial analyst writing a professional daily market report.
Today is ${today}.

Based on these real news headlines from Yahoo Finance, Reuters, CNBC, Seeking Alpha and other financial sources, write a concise daily market report in English.

HEADLINES:
${headlinesText}

Write a structured report with these sections:
1. **Market Overview** (2-3 sentences summarizing the main market mood today)
2. **Key Themes** (3-4 bullet points of the most important themes/events moving markets)
3. **Sector Highlights** (which sectors are in focus and why)
4. **Key Risks & Opportunities** (what to watch)

Be factual, professional, and concise. Base your analysis ONLY on the provided headlines. Do not invent data.`

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 1000,
        messages: [{ role: 'user', content: prompt }]
      }),
      signal: AbortSignal.timeout(30000),
    })

    if (!response.ok) {
      return NextResponse.json({ error: 'Claude API error: ' + response.status }, { status: 500 })
    }

    const data = await response.json()
    const text = data.content?.[0]?.text || 'Unable to generate report.'
    return NextResponse.json({ report: text })
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Unknown error' }, { status: 500 })
  }
}
