'use client'

import { useEffect, useState } from 'react'

export default function NewsPage() {
  const [html, setHtml] = useState('<p style="color:white;padding:20px">Loading...</p>')

  useEffect(() => {
    fetch('/api/news', { cache: 'no-store' })
      .then(r => r.json())
      .then(data => {
        const items = data.world || []
        if (items.length === 0) {
          setHtml('<p style="color:orange;padding:20px">No news returned from API</p>')
          return
        }
        const rows = items.map((n: any) =>
          `<div style="padding:12px 16px;border-left:3px solid #f97316;border-bottom:1px solid rgba(255,255,255,0.05)">
            <a href="${n.link}" target="_blank" style="color:white;text-decoration:none;font-size:13px;line-height:1.6">${n.title}</a>
            <div style="font-size:10px;color:#f97316;margin-top:4px">${n.source}</div>
          </div>`
        ).join('')
        setHtml(`<div style="background:var(--surface);border:1px solid var(--border);border-radius:6px;overflow:hidden">${rows}</div>`)
      })
      .catch(e => setHtml(`<p style="color:red;padding:20px">Error: ${e.message}</p>`))
  }, [])

  return (
    <div className="space-y-4 p-3 fade-in">
      <div className="section-hdr">📰 Global Financial News</div>
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}
