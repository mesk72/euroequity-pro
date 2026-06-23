'use client'

import { useState, useEffect, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import { Stock } from '@/lib/ranking'
import { Plus, Check, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const WALLET_NAMES = ['My Wallet 1', 'My Wallet 2', 'My Wallet 3']

interface Props {
  stock: Stock
  userId: string | null
}

export default function WatchlistButton({ stock, userId }: Props) {
  const [inList, setInList] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!userId) { toast.error('Login required'); return }
    if (inList) {
      // Rimuovi direttamente
      setLoading(true)
      await supabase.from('watchlist')
        .delete()
        .eq('user_id', userId)
        .eq('ticker', stock.ticker)
        .eq('exchange', stock.exchange)
      setInList(false)
      toast.success(`${stock.ticker} removed`)
      setLoading(false)
    } else {
      // Mostra menu wallet
      setShowMenu(true)
    }
  }

  const addToWallet = async (e: React.MouseEvent, walletIdx: number) => {
    e.stopPropagation()
    setShowMenu(false)
    setLoading(true)
    // Verifica limite 50 per wallet
    const { count } = await supabase
      .from('watchlist')
      .select('id', { count: 'exact', head: true })
      .eq('user_id', userId!)
      .eq('wallet', walletIdx)
    if ((count || 0) >= 50) {
      toast.error(`${WALLET_NAMES[walletIdx]} is full (50 max)`)
      setLoading(false)
      return
    }
    await supabase.from('watchlist').insert({
      user_id: userId,
      ticker: stock.ticker,
      exchange: stock.exchange,
      company: stock.company,
      combined_rank: (stock as any).combinedRank ?? null,
      wallet: walletIdx,
    })
    setInList(true)
    toast.success(`${stock.ticker} → ${WALLET_NAMES[walletIdx]}`)
    setLoading(false)
  }

  if (!userId) return null

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={handleClick}
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

      {showMenu && (
        <div style={{
          position: 'absolute', top: 26, left: 0, zIndex: 100,
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 6, boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          minWidth: 130, padding: '4px 0',
        }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', padding: '4px 12px 2px', fontWeight: 700, textTransform: 'uppercase' }}>
            Add to:
          </div>
          {WALLET_NAMES.map((name, idx) => (
            <button key={idx}
              onClick={(e) => addToWallet(e, idx)}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '6px 12px', fontSize: 11, fontWeight: 600,
                color: 'var(--text)', background: 'transparent',
                border: 'none', cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.1)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
