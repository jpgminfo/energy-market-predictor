'use client'

// src/app/dashboard/DashboardClient.tsx

import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const API_BASE = 'http://localhost:8000'

type PriceRow = {
  target_date: string
  trading_slot: number
  area_code: string
  area_price: number
  system_price: number
}

type SummaryRow = {
  target_date: string
  trading_slot: number
  system_price: number
}

// Convert trading slot (1-48) to time label
function slotToTime(slot: number): string {
  const totalMinutes = (slot - 1) * 30
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Format date as MM/DD
function shortDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

type Props = {
  isLoggedIn: boolean
  userEmail: string | null
}

export default function DashboardClient({ isLoggedIn, userEmail }: Props) {
  const [historyData, setHistoryData] = useState<{ date: string; system_price: number }[]>([])
  const [intradayData, setIntradayData] = useState<{ time: string; area_price: number; system_price: number }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [latestDate, setLatestDate] = useState<string>('')

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)

        // Calculate date range — logged in: today, anonymous: yesterday
        const today = new Date()
        const endDate = new Date(today)
        if (!isLoggedIn) endDate.setDate(endDate.getDate() - 1)

        const startDate = new Date(endDate)
        startDate.setDate(startDate.getDate() - 89)

        const fmt = (d: Date) => d.toISOString().split('T')[0]
        const dateFrom = fmt(startDate)
        const dateTo = fmt(endDate)

        // Fetch 30-day system price history
        const histRes = await fetch(
          `${API_BASE}/api/prices/summary?date_from=${dateFrom}&date_to=${dateTo}`
        )
        if (!histRes.ok) throw new Error('Failed to fetch price history')
        const histJson: SummaryRow[] = await histRes.json()

        // Aggregate by date — take average system price per day
        const byDate: Record<string, number[]> = {}
        histJson.forEach(row => {
          if (!byDate[row.target_date]) byDate[row.target_date] = []
          if (row.system_price) byDate[row.target_date].push(row.system_price)
        })

        const history = Object.entries(byDate)
          .map(([date, prices]) => ({
            date: shortDate(date),
            system_price: Math.round((prices.reduce((a, b) => a + b, 0) / prices.length) * 100) / 100,
          }))
          .sort((a, b) => a.date.localeCompare(b.date))

        setHistoryData(history)

        // Fetch latest intraday (only for logged-in users)
        if (isLoggedIn) {
          const intRes = await fetch(`${API_BASE}/api/prices/latest?area=TOKYO`)
          if (!intRes.ok) throw new Error('Failed to fetch intraday data')
          const intJson: PriceRow[] = await intRes.json()

          if (intJson.length > 0) {
            setLatestDate(intJson[0].target_date)
            setIntradayData(
              intJson.map(row => ({
                time: slotToTime(row.trading_slot),
                area_price: row.area_price,
                system_price: row.system_price,
              }))
            )
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [isLoggedIn])

  return (
    <div style={s.root}>
      {/* Nav */}
      <nav style={s.nav}>
        <span style={s.brand}>Information</span>
        <div style={s.navRight}>
          {isLoggedIn ? (
            <>
              <span style={s.navEmail}>{userEmail}</span>
              <form action="/auth/signout" method="post">
                <button style={s.navBtn}>Sign out</button>
              </form>
            </>
          ) : (
            <>
              <a href="/auth/login" style={s.navLink}>Log in</a>
              <a href="/auth/signup" style={s.navBtnPrimary}>Sign up free</a>
            </>
          )}
        </div>
      </nav>

      {/* Main */}
      <main style={s.main}>

        {/* Page header */}
        <div style={s.pageHeader}>
          <h1 style={s.pageTitle}>JEPX</h1>
          <p style={s.pageSubtitle}>
            Spot Market
            {!isLoggedIn && (
              <span style={s.trialNote}> · Showing data up to yesterday</span>
            )}
          </p>
        </div>

        {error && (
          <div style={s.errorBox}>
            Failed to load data: {error}. Make sure the backend is running on port 8000.
          </div>
        )}

        {/* 30-day system price chart */}
        <section style={s.section}>
          <div style={s.sectionHeader}>
            <div>
              <h2 style={s.sectionTitle}>System Price — Last 30 Days</h2>
              <p style={s.sectionSubtitle}>Daily average · ¥/kWh</p>
            </div>
          </div>

          {loading ? (
            <div style={s.skeleton} />
          ) : (
            <div style={s.chartWrap}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={historyData} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#999' }}
                    tickLine={false}
                    axisLine={false}
                    interval={4}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#999' }}
                    tickLine={false}
                    axisLine={false}
                    width={36}
                  />
                  <Tooltip
                    contentStyle={s.tooltip}
                    labelStyle={{ color: '#333', fontWeight: 600, marginBottom: 4 }}
                    formatter={(v) => [`¥${v ?? ''}`, 'System Price']}
                  />
                  <Line
                    type="monotone"
                    dataKey="system_price"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        {/* Intraday chart */}
        <section style={s.section}>
          <div style={s.sectionHeader}>
            <div>
              <h2 style={s.sectionTitle}>Today&apos;s Intraday Curve</h2>
              <p style={s.sectionSubtitle}>
                {isLoggedIn
                  ? `Tokyo area · ${latestDate} · 48 slots · ¥/kWh`
                  : 'Tokyo area · 48 slots · ¥/kWh'}
              </p>
            </div>
          </div>

          {!isLoggedIn ? (
            <div style={s.lockBox}>
              <div style={s.lockIcon}>🔒</div>
              <p style={s.lockTitle}>Today&apos;s prices are available to members</p>
              <p style={s.lockText}>
                Sign up for free to see live intraday prices and unlock full market access.
              </p>
              <a href="/auth/signup" style={s.lockBtn}>Sign up free</a>
              <a href="/auth/login" style={s.lockLink}>Already have an account? Log in</a>
            </div>
          ) : loading ? (
            <div style={s.skeleton} />
          ) : (
            <div style={s.chartWrap}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={intradayData} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 11, fill: '#999' }}
                    tickLine={false}
                    axisLine={false}
                    interval={5}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#999' }}
                    tickLine={false}
                    axisLine={false}
                    width={36}
                  />
                  <Tooltip
                    contentStyle={s.tooltip}
                    labelStyle={{ color: '#333', fontWeight: 600, marginBottom: 4 }}
                    formatter={(value, name) => {
                      const displayValue = Array.isArray(value)
                        ? value.join(', ')
                        : value ?? ''

                      return [
                        `¥${displayValue}`,
                        name === 'area_price' ? 'Tokyo Area Price' : 'System Price',
                      ]
                    }}
                  />
                  <Legend
                    iconType="line"
                    formatter={(v) => v === 'area_price' ? 'Tokyo Area Price' : 'System Price'}
                    wrapperStyle={{ fontSize: 12, color: '#666' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="system_price"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="area_price"
                    stroke="#16a34a"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <footer style={s.footer}>
          Data source: JEPX · Updated daily · {isLoggedIn ? 'Full access' : 'Sign up for today\'s data'}
        </footer>
      </main>
    </div>
  )
}

const s: Record<string, React.CSSProperties> = {
  root: {
    minHeight: '100vh',
    backgroundColor: '#ffffff',
    fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI',
    color: '#111',
  },

  // Nav
  nav: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 2rem',
    height: '56px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fff',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  },
  brand: {
    fontWeight: 700,
    fontSize: '0.95rem',
    letterSpacing: '-0.01em',
    color: '#111',
  },
  navRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  navEmail: {
    fontSize: '0.82rem',
    color: '#666',
  },
  navBtn: {
    padding: '0.35rem 0.85rem',
    fontSize: '0.82rem',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    background: 'transparent',
    cursor: 'pointer',
    color: '#444',
    fontFamily: 'inherit',
  },
  navLink: {
    fontSize: '0.85rem',
    color: '#444',
    textDecoration: 'none',
  },
  navBtnPrimary: {
    padding: '0.35rem 0.9rem',
    fontSize: '0.82rem',
    border: 'none',
    borderRadius: '6px',
    background: '#111',
    color: '#fff',
    cursor: 'pointer',
    textDecoration: 'none',
    fontWeight: 500,
  },

  // Main
  main: {
    maxWidth: '900px',
    margin: '0 auto',
    padding: '2.5rem 2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '2.5rem',
  },
  pageHeader: {
    borderBottom: '1px solid #e5e7eb',
    paddingBottom: '1.25rem',
  },
  pageTitle: {
    fontSize: '1.4rem',
    fontWeight: 700,
    letterSpacing: '-0.02em',
    margin: '0 0 0.3rem',
  },
  pageSubtitle: {
    fontSize: '0.85rem',
    color: '#666',
    margin: 0,
  },
  trialNote: {
    color: '#f59e0b',
  },

  // Sections
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    margin: '0 0 0.2rem',
    letterSpacing: '-0.01em',
  },
  sectionSubtitle: {
    fontSize: '0.78rem',
    color: '#999',
    margin: 0,
  },
  chartWrap: {
    border: '1px solid #e5e7eb',
    borderRadius: '10px',
    padding: '1.25rem 0.5rem 0.5rem',
    backgroundColor: '#fafafa',
  },
  skeleton: {
    height: '280px',
    borderRadius: '10px',
    backgroundColor: '#f3f4f6',
    animation: 'pulse 1.5s ease-in-out infinite',
  },

  // Tooltip
  tooltip: {
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '0.82rem',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    backgroundColor: '#fff',
  },

  // Lock box
  lockBox: {
    border: '1px solid #e5e7eb',
    borderRadius: '10px',
    padding: '3rem 2rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.75rem',
    backgroundColor: '#fafafa',
    textAlign: 'center',
  },
  lockIcon: {
    fontSize: '1.5rem',
    marginBottom: '0.25rem',
  },
  lockTitle: {
    fontSize: '0.95rem',
    fontWeight: 600,
    margin: 0,
    color: '#111',
  },
  lockText: {
    fontSize: '0.83rem',
    color: '#666',
    margin: 0,
    maxWidth: '340px',
    lineHeight: 1.6,
  },
  lockBtn: {
    marginTop: '0.5rem',
    padding: '0.55rem 1.5rem',
    backgroundColor: '#111',
    color: '#fff',
    borderRadius: '7px',
    textDecoration: 'none',
    fontSize: '0.85rem',
    fontWeight: 500,
  },
  lockLink: {
    fontSize: '0.78rem',
    color: '#999',
    textDecoration: 'none',
  },

  // Error
  errorBox: {
    padding: '0.9rem 1.1rem',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    fontSize: '0.83rem',
    color: '#b91c1c',
  },

  // Footer
  footer: {
    fontSize: '0.75rem',
    color: '#bbb',
    textAlign: 'center',
    paddingTop: '1rem',
    borderTop: '1px solid #f3f4f6',
  },
}
