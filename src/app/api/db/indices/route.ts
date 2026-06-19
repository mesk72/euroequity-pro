import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const revalidate = 60

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET() {
  try {
    const { data, error } = await supabase
      .from('indices')
      .select('ticker,name,price,change1d,ytd')

    if (error) {
      console.error('indices error:', error)
      return NextResponse.json({ indices: [], error: error.message })
    }
    if (!data) return NextResponse.json({ indices: [] })

    const indices = data.map((d: any) => ({
      ticker: d.ticker,
      name: d.name,
      close: d.price,
      changeP: d.change1d,
      ytd: d.ytd,
    }))

    return NextResponse.json({ indices })
  } catch (e: any) {
    return NextResponse.json({ indices: [], error: e.message })
  }
}
