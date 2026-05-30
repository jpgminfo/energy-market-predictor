import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

// --- Placeholder data ---
const stats = [
  { label: 'Brent Crude', value: '$84.32', unit: '/bbl', change: '+1.4%', up: true },
  { label: 'Natural Gas', value: '$2.71', unit: '/MMBtu', change: '-0.8%', up: false },
  { label: 'EU Carbon', value: '€61.40', unit: '/tCO₂', change: '+2.1%', up: true },
  { label: 'Power (DE)', value: '€89.50', unit: '/MWh', change: '-3.2%', up: false },
]

const sparkData = {
  'Brent Crude': [78, 80, 79, 82, 81, 83, 84],
  'Natural Gas': [3.1, 2.9, 2.8, 2.75, 2.9, 2.8, 2.71],
  'EU Carbon': [58, 59, 60, 59, 61, 60, 61.4],
  'Power (DE)': [95, 92, 90, 93, 91, 88, 89.5],
}

const predictions = [
  { market: 'Brent Crude', direction: 'Bullish', confidence: 78, horizon: '7d' },
  { market: 'Natural Gas', direction: 'Bearish', confidence: 64, horizon: '3d' },
  { market: 'EU Carbon', direction: 'Bullish', confidence: 81, horizon: '14d' },
  { market: 'Power (DE)', direction: 'Neutral', confidence: 52, horizon: '1d' },
]

const recentActivity = [
  { time: '09:42', event: 'Model retrained on Q2 LNG data', type: 'model' },
  { time: '08:15', event: 'Brent Crude forecast updated', type: 'forecast' },
  { time: 'Yesterday', event: 'New dataset: EU ETS registry', type: 'data' },
  { time: 'Yesterday', event: 'Alert: Gas storage below 5yr avg', type: 'alert' },
]

// --- Spark line SVG helper ---
function Spark({ values, up }: { values: number[]; up: boolean }) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const w = 80
  const h = 28
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w
      const y = h - ((v - min) / range) * h
      return `${x},${y}`
    })
    .join(' ')

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none">
      <polyline
        points={pts}
        stroke={up ? '#22c55e' : '#ef4444'}
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
        opacity="0.9"
      />
    </svg>
  )
}

// --- Confidence bar ---
function ConfidenceBar({ value, direction }: { value: number; direction: string }) {
  const color =
    direction === 'Bullish' ? '#22c55e' :
    direction === 'Bearish' ? '#ef4444' : '#f59e0b'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
      <div style={{ flex: 1, height: '4px', backgroundColor: '#1e1e1e', borderRadius: '999px', overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', backgroundColor: color, borderRadius: '999px', transition: 'width 1s ease' }} />
      </div>
      <span style={{ fontSize: '0.75rem', color, fontWeight: 600, minWidth: '2.5rem', textAlign: 'right' }}>{value}%</span>
    </div>
  )
}

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) redirect('/auth/login')

  const firstName = user.email?.split('@')[0] ?? 'Analyst'

  return (
    <div style={s.root}>
      <style>{css}</style>

      {/* Sidebar */}
      <aside style={s.sidebar}>
        <div style={s.sidebarBrand}>
          <span style={s.brandMark}>⚡</span>
          <span style={s.brandName}>EnergyPredict</span>
        </div>

        <nav style={s.nav}>
          {[
            { icon: '▦', label: 'Dashboard', active: true },
            { icon: '◎', label: 'Markets', active: false },
            { icon: '◈', label: 'Forecasts', active: false },
            { icon: '◉', label: 'Datasets', active: false },
            { icon: '◇', label: 'Settings', active: false },
          ].map(item => (
            <div key={item.label} style={{ ...s.navItem, ...(item.active ? s.navItemActive : {}) }}>
              <span style={s.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div style={s.sidebarFooter}>
          <div style={s.userChip}>
            <div style={s.avatar}>{firstName[0].toUpperCase()}</div>
            <div>
              <div style={s.userName}>{firstName}</div>
              <div style={s.userEmail}>{user.email}</div>
            </div>
          </div>
          <form action="/auth/signout" method="post">
            <button type="submit" style={s.signOutBtn}>Sign out</button>
          </form>
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>

        {/* Header */}
        <header style={s.header}>
          <div>
            <h1 style={s.pageTitle}>Market Overview</h1>
            <p style={s.pageSubtitle}>Live placeholders · Last updated just now</p>
          </div>
          <div style={s.headerBadge}>
            <span style={s.liveDot} />
            Live
          </div>
        </header>

        {/* Stat cards */}
        <section style={s.statsGrid} className="fadeUp">
          {stats.map((stat, i) => (
            <div key={stat.label} style={{ ...s.statCard, animationDelay: `${i * 80}ms` }} className="fadeUp">
              <div style={s.statTop}>
                <span style={s.statLabel}>{stat.label}</span>
                <span style={{ ...s.statChange, color: stat.up ? '#22c55e' : '#ef4444' }}>
                  {stat.up ? '▲' : '▼'} {stat.change}
                </span>
              </div>
              <div style={s.statValue}>
                {stat.value}
                <span style={s.statUnit}>{stat.unit}</span>
              </div>
              <Spark values={sparkData[stat.label as keyof typeof sparkData]} up={stat.up} />
            </div>
          ))}
        </section>

        {/* Lower grid */}
        <section style={s.lowerGrid}>

          {/* Predictions */}
          <div style={s.panel} className="fadeUp">
            <div style={s.panelHeader}>
              <h2 style={s.panelTitle}>AI Predictions</h2>
              <span style={s.panelBadge}>Placeholder</span>
            </div>
            <table style={s.table}>
              <thead>
                <tr>
                  {['Market', 'Direction', 'Horizon', 'Confidence'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {predictions.map(p => (
                  <tr key={p.market} style={s.tr}>
                    <td style={s.td}>{p.market}</td>
                    <td style={s.td}>
                      <span style={{
                        ...s.directionTag,
                        color: p.direction === 'Bullish' ? '#22c55e' : p.direction === 'Bearish' ? '#ef4444' : '#f59e0b',
                        backgroundColor: p.direction === 'Bullish' ? 'rgba(34,197,94,0.08)' : p.direction === 'Bearish' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                        borderColor: p.direction === 'Bullish' ? 'rgba(34,197,94,0.2)' : p.direction === 'Bearish' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)',
                      }}>
                        {p.direction}
                      </span>
                    </td>
                    <td style={{ ...s.td, color: '#555' }}>{p.horizon}</td>
                    <td style={{ ...s.td, minWidth: '140px' }}>
                      <ConfidenceBar value={p.confidence} direction={p.direction} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Activity feed */}
          <div style={s.panel} className="fadeUp">
            <div style={s.panelHeader}>
              <h2 style={s.panelTitle}>Recent Activity</h2>
            </div>
            <div style={s.activityList}>
              {recentActivity.map((item, i) => (
                <div key={i} style={s.activityItem}>
                  <div style={{
                    ...s.activityDot,
                    backgroundColor:
                      item.type === 'alert' ? '#ef4444' :
                      item.type === 'model' ? '#6366f1' :
                      item.type === 'forecast' ? '#22c55e' : '#f59e0b',
                  }} />
                  <div style={s.activityText}>
                    <span style={s.activityEvent}>{item.event}</span>
                    <span style={s.activityTime}>{item.time}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Chart placeholder */}
            <div style={s.chartPlaceholder}>
              <div style={s.chartPlaceholderInner}>
                <span style={s.chartIcon}>◈</span>
                <span style={s.chartPlaceholderText}>Price history chart</span>
                <span style={s.chartPlaceholderSub}>Connect data source to populate</span>
              </div>
              {/* Fake grid lines */}
              {[0,1,2,3].map(i => (
                <div key={i} style={{ ...s.gridLine, top: `${25 * i}%` }} />
              ))}
            </div>
          </div>

        </section>
      </main>
    </div>
  )
}

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }

  .fadeUp {
    animation: fadeUp 0.5s ease both;
  }
`

const s: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: '#080808',
    fontFamily: "'DM Sans', sans-serif",
    color: '#fff',
  },

  // Sidebar
  sidebar: {
    width: '220px',
    flexShrink: 0,
    borderRight: '1px solid #141414',
    display: 'flex',
    flexDirection: 'column',
    padding: '1.5rem 1rem',
    backgroundColor: '#0a0a0a',
  },
  sidebarBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '2.5rem',
    paddingLeft: '0.4rem',
  },
  brandMark: { fontSize: '1.2rem' },
  brandName: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '0.95rem',
    letterSpacing: '-0.02em',
  },
  nav: { display: 'flex', flexDirection: 'column', gap: '0.2rem', flex: 1 },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.65rem',
    padding: '0.55rem 0.75rem',
    borderRadius: '8px',
    fontSize: '0.85rem',
    color: '#444',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  navItemActive: {
    backgroundColor: '#141414',
    color: '#fff',
    border: '1px solid #1e1e1e',
  },
  navIcon: { fontSize: '0.8rem', opacity: 0.7 },
  sidebarFooter: {
    borderTop: '1px solid #141414',
    paddingTop: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  userChip: { display: 'flex', alignItems: 'center', gap: '0.6rem' },
  avatar: {
    width: '30px',
    height: '30px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    fontWeight: 700,
    flexShrink: 0,
  },
  userName: { fontSize: '0.8rem', fontWeight: 500, color: '#ccc' },
  userEmail: { fontSize: '0.68rem', color: '#444', marginTop: '1px' },
  signOutBtn: {
    width: '100%',
    padding: '0.5rem',
    background: 'transparent',
    border: '1px solid #1e1e1e',
    borderRadius: '6px',
    color: '#444',
    fontSize: '0.78rem',
    cursor: 'pointer',
    fontFamily: "'DM Sans', sans-serif",
    transition: 'color 0.15s, border-color 0.15s',
  },

  // Main
  main: {
    flex: 1,
    padding: '2rem',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  pageTitle: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '1.6rem',
    letterSpacing: '-0.03em',
    color: '#fff',
  },
  pageSubtitle: { fontSize: '0.8rem', color: '#444', marginTop: '0.2rem' },
  headerBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    backgroundColor: 'rgba(34,197,94,0.08)',
    border: '1px solid rgba(34,197,94,0.2)',
    borderRadius: '999px',
    padding: '0.3rem 0.75rem',
    fontSize: '0.75rem',
    color: '#22c55e',
    fontWeight: 500,
  },
  liveDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
    animation: 'pulse 1.5s ease-in-out infinite',
  },

  // Stat cards
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1rem',
  },
  statCard: {
    backgroundColor: '#0f0f0f',
    border: '1px solid #1a1a1a',
    borderRadius: '12px',
    padding: '1.1rem 1.2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.4rem',
  },
  statTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  statLabel: { fontSize: '0.75rem', color: '#555', fontWeight: 500 },
  statChange: { fontSize: '0.72rem', fontWeight: 600 },
  statValue: {
    fontSize: '1.45rem',
    fontFamily: "'Syne', sans-serif",
    fontWeight: 700,
    color: '#fff',
    letterSpacing: '-0.02em',
    display: 'flex',
    alignItems: 'baseline',
    gap: '0.2rem',
  },
  statUnit: { fontSize: '0.72rem', color: '#444', fontWeight: 400 },

  // Lower grid
  lowerGrid: {
    display: 'grid',
    gridTemplateColumns: '1.4fr 1fr',
    gap: '1rem',
    flex: 1,
  },
  panel: {
    backgroundColor: '#0f0f0f',
    border: '1px solid #1a1a1a',
    borderRadius: '12px',
    padding: '1.3rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  panelHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  panelTitle: {
    fontFamily: "'Syne', sans-serif",
    fontWeight: 700,
    fontSize: '0.95rem',
    color: '#ccc',
  },
  panelBadge: {
    fontSize: '0.65rem',
    backgroundColor: '#1a1a1a',
    color: '#444',
    padding: '0.2rem 0.55rem',
    borderRadius: '999px',
    border: '1px solid #222',
  },

  // Table
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    textAlign: 'left',
    fontSize: '0.68rem',
    color: '#444',
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    paddingBottom: '0.6rem',
    borderBottom: '1px solid #1a1a1a',
  },
  tr: { borderBottom: '1px solid #111' },
  td: {
    padding: '0.7rem 0',
    fontSize: '0.82rem',
    color: '#bbb',
    paddingRight: '0.75rem',
  },
  directionTag: {
    display: 'inline-block',
    fontSize: '0.72rem',
    fontWeight: 600,
    padding: '0.15rem 0.55rem',
    borderRadius: '999px',
    border: '1px solid',
  },

  // Activity
  activityList: { display: 'flex', flexDirection: 'column', gap: '0.85rem' },
  activityItem: { display: 'flex', alignItems: 'flex-start', gap: '0.75rem' },
  activityDot: {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    marginTop: '0.3rem',
    flexShrink: 0,
  },
  activityText: { display: 'flex', flexDirection: 'column', gap: '0.15rem' },
  activityEvent: { fontSize: '0.8rem', color: '#aaa' },
  activityTime: { fontSize: '0.7rem', color: '#444' },

  // Chart placeholder
  chartPlaceholder: {
    flex: 1,
    minHeight: '120px',
    backgroundColor: '#0a0a0a',
    border: '1px dashed #1e1e1e',
    borderRadius: '8px',
    position: 'relative',
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartPlaceholderInner: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.3rem',
    zIndex: 1,
  },
  chartIcon: { fontSize: '1.4rem', opacity: 0.2 },
  chartPlaceholderText: { fontSize: '0.78rem', color: '#333' },
  chartPlaceholderSub: { fontSize: '0.68rem', color: '#2a2a2a' },
  gridLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: '1px',
    backgroundColor: '#141414',
  },
}
