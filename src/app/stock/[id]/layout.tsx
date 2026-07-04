import { Metadata } from 'next'

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const [ticker, ...exParts] = params.id.split("-")
  const exchangeCode = exParts.join("-")
  try {
    const res = await fetch(
      `https://forwardalpha.pro/api/db/stocks?ticker=${ticker}&exchange=${exchangeCode}`,
      { next: { revalidate: 3600 } }
    )
    const data = await res.json()
    const stock = data.stocks?.[0]
    if (!stock) return { title: `${ticker} | ForwardAlpha` }

    const title = `${stock.company || ticker} (${exchangeCode}) — ${stock.sector || ''} | ForwardAlpha`
    const desc = [
      `${stock.company || ticker} — ${stock.sector || ''} ${stock.country || ''}.`,
      stock.valueScore != null ? `Value Score ${stock.valueScore}.` : '',
      stock.growthScore != null ? `Growth Score ${stock.growthScore}.` : '',
      stock.combinedRank != null ? `Best Score ${stock.combinedRank}.` : '',
      stock.peTrail != null ? `P/E ${stock.peTrail.toFixed(1)}x.` : '',
      stock.pb != null ? `P/B ${stock.pb.toFixed(2)}x.` : '',
      'ForwardAlpha quantitative equity research.',
    ].filter(Boolean).join(' ')

    return {
      title,
      description: desc,
      openGraph: {
        title,
        description: desc,
        url: `https://forwardalpha.pro/stock/${params.id}`,
      },
    }
  } catch {
    return { title: `${ticker} | ForwardAlpha` }
  }
}

export default function StockLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
