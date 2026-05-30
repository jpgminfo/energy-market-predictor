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
    <main style={styles.root}>
      <div style={styles.bg} aria-hidden="true">
        <div style={styles.bgDot1} />
        <div style={styles.bgDot2} />
      </div>

      <div style={styles.card}>
        {/* Brand */}
        <div style={styles.brand}>
          <span style={styles.brandMark}>⚡</span>
          <span style={styles.brandName}>EnergyPredict</span>
        </div>

        <h1 style={styles.heading}>Welcome back</h1>
        <p style={styles.subheading}>Sign in to your account to continue.</p>

        {/* Error */}
        {error && (
          <div style={styles.errorBox}>
            <span style={styles.errorIcon}>!</span>
            {error}
          </div>
        )}

        {/* Email */}
        <div style={styles.field}>
          <label style={styles.label} htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            style={styles.input}
            onFocus={e => Object.assign(e.target.style, styles.inputFocus)}
            onBlur={e => Object.assign(e.target.style, { outline: 'none', borderColor: '#2a2a2a', boxShadow: 'none' })}
          />
        </div>

        {/* Password */}
        <div style={styles.field}>
          <div style={styles.labelRow}>
            <label style={styles.label} htmlFor="password">Password</label>
            <a href="/auth/reset-password" style={styles.forgotLink}>Forgot password?</a>
          </div>
          <div style={styles.inputWrapper}>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="Your password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{ ...styles.input, paddingRight: '2.8rem' }}
              onFocus={e => Object.assign(e.target.style, styles.inputFocus)}
              onBlur={e => Object.assign(e.target.style, { outline: 'none', borderColor: '#2a2a2a', boxShadow: 'none', paddingRight: '2.8rem' })}
            />
            <button
              type="button"
              style={styles.eyeBtn}
              onClick={() => setShowPassword(v => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? '🙈' : '👁'}
            </button>
          </div>
        </div>

        {/* Submit */}
        <button
          style={{ ...styles.submitBtn, opacity: loading ? 0.7 : 1 }}
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? <span style={styles.spinner} /> : null}
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        {/* Divider — ready for OAuth buttons later */}
        <div style={styles.divider}>
          <span style={styles.dividerLine} />
          <span style={styles.dividerText}>or</span>
          <span style={styles.dividerLine} />
        </div>

        {/* OAuth placeholder — wire up providers here later */}
        <button style={styles.oauthBtn} disabled>
          <span>🔒</span>
          Continue with SSO  <span style={styles.comingSoon}>coming soon</span>
        </button>

        <p style={styles.footer}>
          Don&apos;t have an account?{' '}
          <a href="/auth/signup" style={styles.link}>Sign up</a>
        </p>
      </div>

      <style>{keyframes}</style>
    </main>
  )
}

const keyframes = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse1 {
    0%, 100% { transform: scale(1) translate(0, 0); }
    50%       { transform: scale(1.12) translate(10px, -10px); }
  }
  @keyframes pulse2 {
    0%, 100% { transform: scale(1) translate(0, 0); }
    50%       { transform: scale(1.08) translate(-8px, 12px); }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`

const styles: Record<string, React.CSSProperties> = {
  root: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#080808',
    fontFamily: "'DM Sans', sans-serif",
    padding: '1.5rem',
    position: 'relative',
    overflow: 'hidden',
  },
  bg: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    zIndex: 0,
  },
  bgDot1: {
    position: 'absolute',
    width: '480px',
    height: '480px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%)',
    top: '-100px',
    right: '-80px',
    animation: 'pulse1 8s ease-in-out infinite',
  },
  bgDot2: {
    position: 'absolute',
    width: '360px',
    height: '360px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(20,184,166,0.14) 0%, transparent 70%)',
    bottom: '-60px',
    left: '-60px',
    animation: 'pulse2 10s ease-in-out infinite',
  },
  card: {
    position: 'relative',
    zIndex: 1,
    width: '100%',
    maxWidth: '420px',
    backgroundColor: '#0f0f0f',
    border: '1px solid #1e1e1e',
    borderRadius: '16px',
    padding: '2.5rem 2rem',
    animation: 'fadeUp 0.5s ease both',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '2rem',
  },
  brandMark: {
    fontSize: '1.3rem',
  },
  brandName: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '1rem',
    color: '#fff',
    letterSpacing: '-0.02em',
  },
  heading: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '1.9rem',
    color: '#fff',
    margin: '0 0 0.3rem',
    letterSpacing: '-0.03em',
  },
  subheading: {
    fontSize: '0.875rem',
    color: '#555',
    margin: '0 0 1.8rem',
  },
  errorBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.6rem',
    backgroundColor: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: '8px',
    padding: '0.75rem 1rem',
    color: '#ef4444',
    fontSize: '0.82rem',
    marginBottom: '1.2rem',
  },
  errorIcon: {
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    border: '1.5px solid #ef4444',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.7rem',
    fontWeight: 700,
    flexShrink: 0,
  },
  field: {
    marginBottom: '1.1rem',
  },
  labelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.4rem',
  },
  label: {
    display: 'block',
    fontSize: '0.78rem',
    fontWeight: 500,
    color: '#888',
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
  },
  forgotLink: {
    fontSize: '0.78rem',
    color: '#6366f1',
    textDecoration: 'none',
    fontWeight: 500,
  },
  inputWrapper: {
    position: 'relative',
  },
  input: {
    width: '100%',
    backgroundColor: '#141414',
    border: '1px solid #2a2a2a',
    borderRadius: '8px',
    padding: '0.72rem 1rem',
    color: '#fff',
    fontSize: '0.9rem',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    fontFamily: "'DM Sans', sans-serif",
  },
  inputFocus: {
    outline: 'none',
    borderColor: '#6366f1',
    boxShadow: '0 0 0 3px rgba(99,102,241,0.15)',
  },
  eyeBtn: {
    position: 'absolute',
    right: '0.75rem',
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.9rem',
    padding: '0',
    lineHeight: 1,
    opacity: 0.6,
  },
  submitBtn: {
    width: '100%',
    padding: '0.82rem',
    marginTop: '0.6rem',
    background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.92rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: "'DM Sans', sans-serif",
    letterSpacing: '0.01em',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    transition: 'opacity 0.2s',
  },
  spinner: {
    width: '14px',
    height: '14px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
    display: 'inline-block',
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    margin: '1.4rem 0 1rem',
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    backgroundColor: '#1e1e1e',
  },
  dividerText: {
    fontSize: '0.75rem',
    color: '#444',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  oauthBtn: {
    width: '100%',
    padding: '0.78rem',
    background: 'transparent',
    color: '#444',
    border: '1px solid #1e1e1e',
    borderRadius: '8px',
    fontSize: '0.88rem',
    fontWeight: 500,
    cursor: 'not-allowed',
    fontFamily: "'DM Sans', sans-serif",
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
  },
  comingSoon: {
    fontSize: '0.7rem',
    backgroundColor: '#1e1e1e',
    color: '#555',
    padding: '0.15rem 0.5rem',
    borderRadius: '999px',
    marginLeft: '0.3rem',
  },
  footer: {
    textAlign: 'center',
    fontSize: '0.82rem',
    color: '#555',
    marginTop: '1.4rem',
  },
  link: {
    color: '#6366f1',
    textDecoration: 'none',
    fontWeight: 500,
  },
}
