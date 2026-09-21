'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  async function handleLogin() {
    setError(null)
    setLoading(true)
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      setError(error.message)
    } else {
      router.push('/dashboard')
      router.refresh()
    }
  }

  async function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') await handleLogin()
  }

  return (
    <div style={s.root}>
      <nav style={s.nav}>
        <a href="/dashboard" style={s.brand}>Information</a>
      </nav>

      <main style={s.main}>
        <div style={s.card}>
          <h1 style={s.heading}>Sign in</h1>
          <p style={s.sub}>
            Don&apos;t have an account?{' '}
            <a href="/auth/signup" style={s.link}>Sign up free</a>
          </p>

          {error && <div style={s.error}>{error}</div>}

          <div style={s.field}>
            <label style={s.label} htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              style={s.input}
            />
          </div>

          <div style={s.field}>
            <div style={s.labelRow}>
              <label style={s.label} htmlFor="password">Password</label>
              <a href="/auth/reset-password" style={s.forgotLink}>Forgot password?</a>
            </div>
            <div style={s.inputWrap}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={handleKeyDown}
                style={{ ...s.input, paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                style={s.eyeBtn}
                onClick={() => setShowPassword(v => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '○' : '●'}
              </button>
            </div>
          </div>

          <button
            style={{ ...s.submitBtn, opacity: loading ? 0.6 : 1 }}
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
      </main>
    </div>
  )
}

const s: Record<string, React.CSSProperties> = {
  root: {
    minHeight: '100vh',
    backgroundColor: '#ffffff',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    color: '#111',
  },
  nav: {
    height: '56px',
    padding: '0 2rem',
    display: 'flex',
    alignItems: 'center',
    borderBottom: '1px solid #e5e7eb',
  },
  brand: {
    fontWeight: 700,
    fontSize: '0.95rem',
    color: '#111',
    textDecoration: 'none',
    letterSpacing: '-0.01em',
  },
  main: {
    display: 'flex',
    justifyContent: 'center',
    padding: '4rem 1.5rem',
  },
  card: {
    width: '100%',
    maxWidth: '380px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  heading: {
    fontSize: '1.4rem',
    fontWeight: 700,
    letterSpacing: '-0.02em',
    margin: '0 0 0.1rem',
  },
  sub: {
    fontSize: '0.85rem',
    color: '#666',
    margin: '0 0 0.5rem',
  },
  link: {
    color: '#2563eb',
    textDecoration: 'none',
    fontWeight: 500,
  },
  forgotLink: {
    color: '#666',
    textDecoration: 'none',
    fontSize: '0.78rem',
  },
  error: {
    padding: '0.75rem 1rem',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    fontSize: '0.83rem',
    color: '#b91c1c',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem',
  },
  labelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: '0.82rem',
    fontWeight: 500,
    color: '#374151',
  },
  inputWrap: {
    position: 'relative',
  },
  input: {
    width: '100%',
    padding: '0.65rem 0.9rem',
    border: '1px solid #e5e7eb',
    borderRadius: '7px',
    fontSize: '0.9rem',
    outline: 'none',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
    color: '#111',
    backgroundColor: '#fff',
    transition: 'border-color 0.15s',
  },
  eyeBtn: {
    position: 'absolute',
    right: '0.75rem',
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.75rem',
    color: '#999',
    padding: 0,
    lineHeight: 1,
  },
  submitBtn: {
    width: '100%',
    padding: '0.7rem',
    marginTop: '0.25rem',
    backgroundColor: '#111',
    color: '#fff',
    border: 'none',
    borderRadius: '7px',
    fontSize: '0.9rem',
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'opacity 0.15s',
  },
}
