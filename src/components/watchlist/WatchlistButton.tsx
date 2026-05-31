'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Stock } from '@/lib/ranking'
import { Plus, Check, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface Props {
  stock: Stock
  userId: string | null
}

export default function WatchlistButton({ stock, userId }: Props) {
  const [inList, setInList] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    supabase
      .from('watchlist')
      .select('id')
      .eq('user_id', userId)
      .eq('ticker', stock.ticker)
      .eq('exchange', stock.exchange)
      .maybeSingle()
      .then(({ data }) => setInList(!!data))
  }, [userId, stock.ticker, stock.exchange])

  const toggle = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!userId) { toast.error('Login required'); return }
    setLoading(true)
    if (inList) {
      await supabase.from('watchlist')
        .delete()
        .eq('user_id', userId)
        .eq('ticker', stock.ticker)
        .eq('exchange', stock.exchange)
      setInList(false)
      toast.success(`${stock.ticker} removed from My Screen`)
    } else {
      // Verifica limite 50
      const { count } = await supabase
        .from('watchlist')
        .select('id', { count: 'exact', head: true })
        .eq('user_id', userId)
      if ((count || 0) >= 50) {
        toast.error('My Screen is full (50 stocks max)')
        setLoading(false)
        return
      }
      await supabase.from('watchlist').insert({
        user_id: userId,
        ticker: stock.ticker,
        exchange: stock.exchange,
        company: stock.company,
        combined_rank: (stock as any).combinedRank ?? null,
      })
      setInList(true)
      toast.success(`${stock.ticker} added to My Screen`)
    }
    setLoading(false)
  }

  if (!userId) return null

  return (
    <button
      onClick={toggle}
      title={inList ? 'Remove from My Screen' : 'Add to My Screen'}
      style={{
        width: 22, height: 22, borderRadius: 4, flexShrink: 0,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        border: inList ? '1px solid var(--green)' : '1px solid var(--border)',
        background: inList ? 'rgba(34,196,138,0.1)' : 'transparent',
        cursor: loading ? 'wait' : 'pointer',
        transition: 'all 0.15s',
      }}>
      {loading
        ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />
        : inList
          ? <Check size={11} style={{ color: 'var(--green)' }} />
          : <Plus size={11} style={{ color: 'var(--text3)' }} />
      }
    </button>
  )
}
