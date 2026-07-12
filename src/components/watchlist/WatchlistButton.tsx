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
  // Prima teneva solo un booleano "e' in qualche wallet" — impediva di
  // aggiungere lo stesso titolo a un secondo wallet, perche' il pulsante
  // diventava "rimuovi" appena era presente in uno qualsiasi. Ora tiene
  // traccia di QUALI wallet specifici contengono il titolo.
  const [walletSet, setWalletSet] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const refresh = () => {
    if (!userId) return
    supabase
      .from('watchlist')
      .select('wallet')
      .eq('user_id', userId)
      .eq('ticker', stock.ticker)
      .eq('exchange', stock.exchange)
      .then(({ data }) => setWalletSet(new Set((data || []).map((d: any) => d.wallet ?? 0))))
  }

  useEffect(() => { refresh() }, [userId, stock.ticker, stock.exchange])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const toggleWallet = async (e: React.MouseEvent, walletIdx: number) => {
    e.stopPropagation()
    if (!userId) return
    setLoading(true)
    if (walletSet.has(walletIdx)) {
      // Rimuovi SOLO da questo wallet, non dagli altri
      await supabase.from('watchlist')
        .delete()
        .eq('user_id', userId)
        .eq('ticker', stock.ticker)
        .eq('exchange', stock.exchange)
        .eq('wallet', walletIdx)
      const next = new Set(walletSet); next.delete(walletIdx)
      setWalletSet(next)
      toast.success(`${stock.ticker} removed from ${WALLET_NAMES[walletIdx]}`)
    } else {
      const { count } = await supabase
        .from('watchlist')
        .select('id', { count: 'exact', head: true })
        .eq('user_id', userId)
        .eq('wallet', walletIdx)
      if ((count || 0) >= 100) {
        toast.error(`${WALLET_NAMES[walletIdx]} is full (100 max)`)
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
      const next = new Set(walletSet); next.add(walletIdx)
      setWalletSet(next)
      toast.success(`${stock.ticker} → ${WALLET_NAMES[walletIdx]}`)
    }
    setLoading(false)
  }

  if (!userId) return null
  const inList = walletSet.size > 0

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={(e) => { e.stopPropagation(); setShowMenu(v => !v) }}
        title={inList ? `In ${walletSet.size} wallet${walletSet.size > 1 ? 's' : ''} — click to manage` : 'Add to My Screen'}
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
          minWidth: 150, padding: '4px 0',
        }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', padding: '4px 12px 2px', fontWeight: 700, textTransform: 'uppercase' }}>
            Wallets (can select more than one):
          </div>
          {WALLET_NAMES.map((name, idx) => (
            <button key={idx}
              onClick={(e) => toggleWallet(e, idx)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left',
                padding: '6px 12px', fontSize: 11, fontWeight: 600,
                color: 'var(--text)', background: 'transparent',
                border: 'none', cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'rgba(249,115,22,0.1)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
              <span style={{
                width: 14, height: 14, borderRadius: 3, flexShrink: 0,
                border: walletSet.has(idx) ? '1px solid var(--green)' : '1px solid var(--border)',
                background: walletSet.has(idx) ? 'var(--green)' : 'transparent',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {walletSet.has(idx) && <Check size={10} style={{ color: '#000' }} />}
              </span>
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
