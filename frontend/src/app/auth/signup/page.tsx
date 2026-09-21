'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SignUpPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  async function handleSignUp() {
    setError(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    const supabase = createClient()
    const { error } = await supabase.auth.signUp({ email, password })
    setLoading(false)

    if (error) {
      setError(error.message)
    } else {
      router.push('/dashboard')
    }
  }

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword

  return (
    <div style={s.root}>
      <nav style={s.nav}>
        <a href="/dashboard" style={s.brand}>Information</a>
      </nav>

      <main style={s.main}>
        <div style={s.card}>
          <h1 style={s.heading}>Create account</h1>
          <p style={s.sub}>
            Already have an account?{' '}
            <a href="/auth/login" style={s.link}>Sign in</a>
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
              style={s.input}
            />
          </div>

          <div style={s.field}>
            <label style={s.label} htmlFor="password">Password</label>
            <div style={s.inputWrap}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="8 characters minimum"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ ...s.input, paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                style={s.eyeBtn}
                onClick={() => setShowPassword(v => !v)}
                aria-label={showPassword ? 'Hide' : 'Show'}
              >
                {showPassword ? '○' : '●'}
              </button>
            </div>
            {password.length > 0 && <StrengthBar password={password} />}
          </div>

          <div style={s.field}>
            <label style={s.label} htmlFor="confirm">Confirm password</label>
            <div style={s.inputWrap}>
              <input
                id="confirm"
                type={showConfirm ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Repeat your password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                style={{
                  ...s.input,
                  paddingRight: '2.75rem',
                  borderColor: passwordsMatch
                    ? '#16a34a'
                    : passwordsMismatch
                    ? '#dc2626'
                    : '#e5e7eb',
                }}
              />
              <button
                type="button"
                style={s.eyeBtn}
                onClick={() => setShowConfirm(v => !v)}
                aria-label={showConfirm ? 'Hide' : 'Show'}
              >
                {showConfirm ? '○' : '●'}
              </button>
            </div>
          </div>

          <button
            style={{ ...s.submitBtn, opacity: loading ? 0.6 : 1 }}
            onClick={handleSignUp}
            disabled={loading}
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>

          <p style={s.terms}>
            By signing up you agree to our{' '}
            <a href="#" style={s.link}>Terms</a> and{' '}
            <a href="#" style={s.link}>Privacy Policy</a>.
          </p>
        </div>
      </main>
    </div>
  )
}

function StrengthBar({ password }: { password: string }) {
  const score = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length

  const labels = ['Weak', 'Fair', 'Good', 'Strong']
  const colors = ['#dc2626', '#f97316', '#ca8a04', '#16a34a']

  return (
    <div style={{ marginTop: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
      <div style={{ display: 'flex', gap: '3px' }}>
        {[0, 1, 2, 3].map(i => (
          <div
            key={i}
            style={{
              flex: 1,
              height: '3px',
              borderRadius: '999px',
              backgroundColor: i < score ? colors[score - 1] : '#e5e7eb',
              transition: 'background-color 0.2s',
            }}
          />
        ))}
      </div>
      {score > 0 && (
        <span style={{ fontSize: '0.72rem', color: colors[score - 1] }}>
          {labels[score - 1]}
        </span>
      )}
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
  terms: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    textAlign: 'center',
    margin: 0,
  },
}
