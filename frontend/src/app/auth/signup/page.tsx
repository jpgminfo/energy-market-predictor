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
  const [success, setSuccess] = useState(false)
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
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/confirm`,
      },
    })

    setLoading(false)

    if (error) {
      setError(error.message)
    } else {
      setSuccess(true)
    }
  }

  if (success) {
    return (
      <main style={styles.root}>
        <div style={styles.card}>
          <div style={styles.successIcon}>✓</div>
          <h2 style={styles.successTitle}>Check your email</h2>
          <p style={styles.successText}>
            We sent a confirmation link to <strong>{email}</strong>.<br />
            Click it to activate your account.
          </p>
          <button style={styles.outlineButton} onClick={() => router.push('/auth/login')}>
            Go to Sign In
          </button>
        </div>
        <style>{keyframes}</style>
      </main>
    )
  }

  return (
    <main style={styles.root}>
      <div style={styles.bg} aria-hidden="true">
        <div style={styles.bgDot1} />
        <div style={styles.bgDot2} />
      </div>

      <div style={styles.card}>
        {/* Logo / Brand */}
        <div style={styles.brand}>
          <span style={styles.brandMark}>⚡</span>
          <span style={styles.brandName}>EnergyPredict</span>
        </div>

        <h1 style={styles.heading}>Create account</h1>
        <p style={styles.subheading}>Start predicting energy markets today.</p>

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
            style={styles.input}
            onFocus={e => Object.assign(e.target.style, styles.inputFocus)}
            onBlur={e => Object.assign(e.target.style, { outline: 'none', borderColor: '#2a2a2a', boxShadow: 'none' })}
          />
        </div>

        {/* Password */}
        <div style={styles.field}>
          <label style={styles.label} htmlFor="password">Password</label>
          <div style={styles.inputWrapper}>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={e => setPassword(e.target.value)}
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
          {password.length > 0 && (
            <PasswordStrength password={password} />
          )}
        </div>

        {/* Confirm Password */}
        <div style={styles.field}>
          <label style={styles.label} htmlFor="confirm">Confirm Password</label>
          <div style={styles.inputWrapper}>
            <input
              id="confirm"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Repeat your password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              style={{
                ...styles.input,
                paddingRight: '2.8rem',
                borderColor: confirmPassword.length > 0
                  ? confirmPassword === password ? '#22c55e' : '#ef4444'
                  : '#2a2a2a',
              }}
              onFocus={e => Object.assign(e.target.style, styles.inputFocus)}
              onBlur={e => {
                e.target.style.outline = 'none'
                e.target.style.boxShadow = 'none'
                e.target.style.borderColor = confirmPassword.length > 0
                  ? confirmPassword === password ? '#22c55e' : '#ef4444'
                  : '#2a2a2a'
                e.target.style.paddingRight = '2.8rem'
              }}
            />
            <button
              type="button"
              style={styles.eyeBtn}
              onClick={() => setShowConfirm(v => !v)}
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
            >
              {showConfirm ? '🙈' : '👁'}
            </button>
          </div>
        </div>

        {/* Submit */}
        <button
          style={{ ...styles.submitBtn, opacity: loading ? 0.7 : 1 }}
          onClick={handleSignUp}
          disabled={loading}
        >
          {loading ? <span style={styles.spinner} /> : null}
          {loading ? 'Creating account…' : 'Create account'}
        </button>

        <p style={styles.footer}>
          Already have an account?{' '}
          <a href="/auth/login" style={styles.link}>Sign in</a>
        </p>
      </div>

      <style>{keyframes}</style>
    </main>
  )
}

function PasswordStrength({ password }: { password: string }) {
  const score = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length

  const labels = ['Weak', 'Fair', 'Good', 'Strong']
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e']

  return (
    <div style={{ marginTop: '0.4rem' }}>
      <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
        {[0, 1, 2, 3].map(i => (
          <div
            key={i}
            style={{
              flex: 1,
              height: '3px',
              borderRadius: '999px',
              backgroundColor: i < score ? colors[score - 1] : '#2a2a2a',
              transition: 'background-color 0.3s ease',
            }}
          />
        ))}
      </div>
      <span style={{ fontSize: '0.7rem', color: score > 0 ? colors[score - 1] : '#555' }}>
        {score > 0 ? labels[score - 1] : ''}
      </span>
    </div>
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
  label: {
    display: 'block',
    fontSize: '0.78rem',
    fontWeight: 500,
    color: '#888',
    marginBottom: '0.4rem',
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
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
  successIcon: {
    width: '52px',
    height: '52px',
    borderRadius: '50%',
    backgroundColor: 'rgba(34,197,94,0.1)',
    border: '1px solid rgba(34,197,94,0.3)',
    color: '#22c55e',
    fontSize: '1.4rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '1.2rem',
  },
  successTitle: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '1.5rem',
    color: '#fff',
    margin: '0 0 0.6rem',
  },
  successText: {
    fontSize: '0.875rem',
    color: '#777',
    lineHeight: 1.6,
    marginBottom: '1.6rem',
  },
  outlineButton: {
    width: '100%',
    padding: '0.82rem',
    background: 'transparent',
    color: '#fff',
    border: '1px solid #2a2a2a',
    borderRadius: '8px',
    fontSize: '0.92rem',
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: "'DM Sans', sans-serif",
  },
}
