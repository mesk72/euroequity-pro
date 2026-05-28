'use client'

import { useState } from 'react'
import { supabase, createProfile, ensureDefaultPortfolios } from '@/lib/supabase'
import toast from 'react-hot-toast'
import { X, Eye, EyeOff } from 'lucide-react'

const COUNTRIES = [
  'Italy','Germany','France','Netherlands','Spain','Belgium','Portugal',
  'Austria','Finland','Ireland','Greece','United Kingdom','Switzerland',
  'Sweden','Norway','Denmark','United States','Other'
]

interface Props {
  onClose: () => void
  onSuccess: () => void
}

export default function AuthModal({ onClose, onSuccess }: Props) {
  const [mode,       setMode]       = useState<'login'|'register'>('login')
  const [email,      setEmail]      = useState('')
  const [password,   setPassword]   = useState('')
  const [name,       setName]       = useState('')
  const [country,    setCountry]    = useState('Italy')
  const [showPw,     setShowPw]     = useState(false)
  const [loading,    setLoading]    = useState(false)
  const [gdpr,       setGdpr]       = useState(false)
  const [newsletter, setNewsletter] = useState(false)
  const [sent,       setSent]       = useState(false)

  async function handleLogin() {
    if (!email || !password) { toast.error('Please enter email and password.'); return }
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      if (error.message.includes('Invalid login')) {
        toast.error('Invalid email or password.')
      } else if (error.message.includes('Email not confirmed')) {
        toast.error('Please confirm your email first. Check your inbox.')
      } else {
        toast.error(error.message)
      }
    } else {
      toast.success('Welcome back!')
      onSuccess()
      window.location.reload()
    }
  }

  async function handleRegister() {
    if (!gdpr)           { toast.error('Please accept the Terms of Use and Privacy Policy.'); return }
    if (!name.trim())    { toast.error('Please enter your name.'); return }
    if (!email)          { toast.error('Please enter your email.'); return }
    if (password.length < 8) { toast.error('Password must be at least 8 characters.'); return }

    setLoading(true)
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: 'https://forwardalpha.pro',
        data: { name, country, newsletter }
      }
    })

    if (error) {
      toast.error(error.message)
      setLoading(false)
      return
    }

    if (data.user) {
      try {
        await createProfile(data.user.id, email, name, country)
        await ensureDefaultPortfolios(data.user.id)
      } catch {}
    }

    setLoading(false)
    setSent(true)
  }

  async function handleForgotPassword() {
    if (!email) { toast.error('Please enter your email first.'); return }
    setLoading(true)
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: 'https://forwardalpha.pro',
    })
    setLoading(false)
    if (error) { toast.error(error.message) }
    else { toast.success('Password reset email sent. Check your inbox.') }
  }

  if (sent) {
    return (
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
        <div className="bg-surface border border-border rounded-lg p-8 w-full max-w-md text-center">
          <div style={{ fontSize: 48, marginBottom: 16 }}>📧</div>
          <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 20, color: 'var(--text)', marginBottom: 8 }}>
            Check your inbox
          </div>
          <div style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 24, lineHeight: 1.6 }}>
            We sent a confirmation link to <strong>{email}</strong>.<br />
            Click the link to activate your account and log in.
          </div>
          <button onClick={onClose}
            style={{ background: 'var(--orange)', color: '#fff', fontFamily: 'IBM Plex Sans Condensed',
              fontWeight: 700, fontSize: 14, padding: '10px 24px', borderRadius: 4, border: 'none', cursor: 'pointer' }}>
            Got it
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-surface border border-border rounded-lg p-6 w-full max-w-md relative"
        style={{ maxHeight: '90vh', overflowY: 'auto' }}>
        <button onClick={onClose} className="absolute top-4 right-4 text-muted hover:text-text">
          <X size={18} />
        </button>

        {/* Logo */}
        <div className="text-center mb-6">
          <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 22, color: 'var(--text)' }}>
            FORWARD<span style={{ color: 'var(--orange)' }}>ALPHA</span>
          </div>
          <div className="text-xs text-muted mt-1">Professional European Equity Research</div>
        </div>

        {/* Tabs */}
        <div className="flex mb-6 border border-border rounded-lg overflow-hidden">
          {(['login', 'register'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)}
              className={`flex-1 py-2.5 text-sm font-600 transition-colors ${
                mode === m ? 'bg-orange-500 text-white' : 'text-muted hover:text-text'
              }`}
              style={{ background: mode === m ? 'var(--orange)' : 'transparent' }}>
              {m === 'login' ? 'Log In' : 'Register Free'}
            </button>
          ))}
        </div>

        <div className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="text-xs text-muted font-700 uppercase tracking-wide">Full Name *</label>
              <input value={name} onChange={e => setName(e.target.value)}
                placeholder="Your full name" className="input-field mt-1"
                onKeyDown={e => e.key === 'Enter' && handleRegister()} />
            </div>
          )}

          <div>
            <label className="text-xs text-muted font-700 uppercase tracking-wide">Email *</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com" className="input-field mt-1"
              onKeyDown={e => e.key === 'Enter' && (mode === 'login' ? handleLogin() : handleRegister())} />
          </div>

          <div>
            <label className="text-xs text-muted font-700 uppercase tracking-wide">Password *</label>
            <div className="relative mt-1">
              <input type={showPw ? 'text' : 'password'} value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Min 8 characters' : '••••••••'}
                className="input-field pr-10"
                onKeyDown={e => e.key === 'Enter' && (mode === 'login' ? handleLogin() : handleRegister())} />
              <button onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted" type="button">
                {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            {mode === 'login' && (
              <button onClick={handleForgotPassword}
                className="text-xs text-muted hover:text-orange-400 mt-1 float-right" type="button">
                Forgot password?
              </button>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="text-xs text-muted font-700 uppercase tracking-wide">Country</label>
              <select value={country} onChange={e => setCountry(e.target.value)} className="input-field mt-1">
                {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          )}

          {mode === 'register' && (
            <div className="space-y-3 pt-2">
              <label className="flex items-start gap-2 cursor-pointer">
                <input type="checkbox" checked={gdpr} onChange={e => setGdpr(e.target.checked)} className="mt-0.5" />
                <span className="text-xs text-muted leading-relaxed">
                  I have read and agree to the{' '}
                  <a href="/legal" target="_blank" className="text-orange-400 underline">Terms of Use and Privacy Policy</a>. *
                </span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input type="checkbox" checked={newsletter} onChange={e => setNewsletter(e.target.checked)} className="mt-0.5" />
                <span className="text-xs text-muted">
                  Receive product updates and market insights from ForwardAlpha. Unsubscribe anytime.
                </span>
              </label>
            </div>
          )}

          <button onClick={mode === 'login' ? handleLogin : handleRegister}
            disabled={loading}
            className="w-full font-700 py-3 rounded-lg text-sm transition-colors disabled:opacity-50"
            style={{ background: 'var(--orange)', color: '#fff', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Loading…' : mode === 'login' ? 'Log In' : 'Create Free Account'}
          </button>

          {mode === 'register' && (
            <p className="text-xs text-muted text-center">
              14-day free trial · No credit card required · Cancel anytime
            </p>
          )}

          <div className="text-center pt-2">
            {mode === 'login' ? (
              <span className="text-xs text-muted">
                No account?{' '}
                <button onClick={() => setMode('register')} className="text-orange-400 hover:underline">
                  Register free
                </button>
              </span>
            ) : (
              <span className="text-xs text-muted">
                Already have an account?{' '}
                <button onClick={() => setMode('login')} className="text-orange-400 hover:underline">
                  Log in
                </button>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
