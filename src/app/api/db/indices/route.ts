import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET() {
  try {
    const { data, error } = await supabase
      .from('indices_live')
      .select('ticker,name,close,change_pct')

    if (error || !data) return NextResponse.json({ indices: [] })

    const indices = data.map((d: any) => ({
      ticker: d.ticker,
      name: d.name,
      close: d.close,
      changeP: d.change_pct,
    }))

    return NextResponse.json({ indices })
  } catch {
    return NextResponse.json({ indices: [] })
  }
}
