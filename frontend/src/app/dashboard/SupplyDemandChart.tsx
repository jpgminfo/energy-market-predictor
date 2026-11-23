'use client'

// src/app/dashboard/SupplyDemandChart.tsx
// One area, one day: generation by source (stacked) against demand.

import { useEffect, useState } from 'react'
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

type ValueKey =
  | 'area_demand' | 'nuclear' | 'thermal_total' | 'hydro' | 'geothermal'
  | 'biomass_actual' | 'solar_actual' | 'wind_actual'
  | 'pumped_storage' | 'battery' | 'interconnection'

type Row = { time: string; trading_slot: number; interval_minutes: number } &
  Record<ValueKey, number | null>

type Response = { area: string; date: string; latest_date: string | null; rows: Row[] }
type RequestState =
  | { key: string; response: Response }
  | { key: string; error: string }

// Stacked from the bottom: steady sources first, solar on top.
// `group` is what a renewable vs non-renewable view will sum over later.
type Group = 'renewable' | 'nuclear' | 'thermal'
const STACK: { key: ValueKey; label: string; color: string; group: Group }[] = [
  { key: 'nuclear',        label: 'Nuclear',    color: '#7c3aed', group: 'nuclear' },
  { key: 'thermal_total',  label: 'Thermal',    color: '#78716c', group: 'thermal' },
  { key: 'hydro',          label: 'Hydro',      color: '#0ea5e9', group: 'renewable' },
  { key: 'geothermal',     label: 'Geothermal', color: '#b45309', group: 'renewable' },
  { key: 'biomass_actual', label: 'Biomass',    color: '#65a30d', group: 'renewable' },
  { key: 'wind_actual',    label: 'Wind',       color: '#14b8a6', group: 'renewable' },
  { key: 'solar_actual',   label: 'Solar',      color: '#f59e0b', group: 'renewable' },
]

// These can be negative, so they are drawn as lines instead of in the stack.
const FLOWS: { key: ValueKey; label: string; color: string }[] = [
  { key: 'pumped_storage',  label: 'Pumped storage',  color: '#2563eb' },
  { key: 'battery',         label: 'Battery',         color: '#db2777' },
  { key: 'interconnection', label: 'Interconnection', color: '#475569' },
]

const AREAS: [string, string][] = [
  ['HOKKAIDO', 'Hokkaido'], ['TOHOKU', 'Tohoku'], ['TOKYO', 'Tokyo'],
  ['CHUBU', 'Chubu'], ['HOKURIKU', 'Hokuriku'], ['KANSAI', 'Kansai'],
  ['CHUGOKU', 'Chugoku'], ['SHIKOKU', 'Shikoku'], ['KYUSHU', 'Kyushu'],
]

function localDate(offsetDays = 0): string {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

export default function SupplyDemandChart() {
  const [area, setArea] = useState('TOKYO')
  const [date, setDate] = useState(localDate(-1))
  const [request, setRequest] = useState<RequestState | null>(null)
  const requestKey = `${area}:${date}`

  useEffect(() => {
    const ctrl = new AbortController()
    const key = `${area}:${date}`
    fetch(`${API_BASE}/api/supply-demand?area=${area}&date=${date}`, { signal: ctrl.signal })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<Response>
      })
      .then(response => {
        if (!ctrl.signal.aborted) setRequest({ key, response })
      })
      .catch(e => {
        if (!ctrl.signal.aborted && e.name !== 'AbortError') {
          setRequest({ key, error: e.message })
        }
      })
    return () => ctrl.abort()
  }, [area, date])

  const currentRequest = request?.key === requestKey ? request : null
  const resp = currentRequest && 'response' in currentRequest ? currentRequest.response : null
  const error = currentRequest && 'error' in currentRequest ? currentRequest.error : null
  const loading = currentRequest === null
  const rows = resp?.rows ?? []
  // A series that is NULL for the whole day was not reported: leave it out
  // instead of drawing it as zero.
  const stack = STACK.filter(s => rows.some(r => r[s.key] != null))
  const flows = FLOWS.filter(f => rows.some(r => r[f.key] != null))
  const hasValues = stack.length > 0 || rows.some(r => r.area_demand != null)
  const data = rows.map(r => ({
    ...r,
    ...Object.fromEntries(stack.map(s => [s.key, r[s.key] ?? 0])),
  }))
  const areaName = AREAS.find(([code]) => code === area)?.[1] ?? area
  const tickSkip = Math.max(Math.round(data.length / 8) - 1, 0)

  return (
    <section style={s.section}>
      <div style={s.header}>
        <div>
          <h2 style={s.title}>Supply and demand by source</h2>
          <p style={s.subtitle}>{areaName} · {date} · MW average</p>
        </div>
        <div style={s.controls}>
          <select value={area} onChange={e => setArea(e.target.value)} style={s.input}
                  aria-label="Area">
            {AREAS.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
          <input type="date" value={date} onChange={e => e.target.value && setDate(e.target.value)}
                 style={s.input} aria-label="Date" />
        </div>
      </div>

      {error ? (
        <div style={s.error}>Could not load data ({error}). Check that the API is running.</div>
      ) : loading ? (
        <div style={s.skeleton} />
      ) : rows.length === 0 ? (
        <div style={s.empty}>
          <p style={s.emptyText}>No data for {areaName} on {date}.</p>
          {resp?.latest_date && (
            <button style={s.button} onClick={() => setDate(resp.latest_date!)}>
              Show latest available ({resp.latest_date})
            </button>
          )}
        </div>
      ) : !hasValues ? (
        <div style={s.empty}>
          <p style={s.emptyText}>
            The source file has rows for {date} but no reported values yet.
          </p>
        </div>
      ) : (
        <div style={s.chartWrap}>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#999' }} tickLine={false}
                     axisLine={false} interval={tickSkip} />
              <YAxis tick={{ fontSize: 11, fill: '#999' }} tickLine={false} axisLine={false}
                     width={48} tickFormatter={(v: number) => v.toLocaleString()} />
              <Tooltip contentStyle={s.tooltip}
                       formatter={v => `${Number(v).toLocaleString()} MW`} />
              <Legend iconType="line" wrapperStyle={{ fontSize: 12, color: '#666' }} />
              {stack.map(src => (
                <Area key={src.key} type="monotone" dataKey={src.key} name={src.label}
                      stackId="supply" stroke={src.color} fill={src.color} fillOpacity={0.55}
                      strokeWidth={1} isAnimationActive={false} />
              ))}
              {flows.map(f => (
                <Line key={f.key} type="monotone" dataKey={f.key} name={f.label}
                      stroke={f.color} strokeWidth={1.5} strokeDasharray="4 3" dot={false}
                      isAnimationActive={false} />
              ))}
              <Line type="monotone" dataKey="area_demand" name="Demand" stroke="#111"
                    strokeWidth={2} dot={false} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

const s: Record<string, React.CSSProperties> = {
  section: { display: 'flex', flexDirection: 'column', gap: '1rem' },
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
            gap: '1rem', flexWrap: 'wrap' },
  title: { fontSize: '1rem', fontWeight: 600, margin: '0 0 0.2rem', letterSpacing: '-0.01em' },
  subtitle: { fontSize: '0.78rem', color: '#999', margin: 0 },
  controls: { display: 'flex', gap: '0.5rem' },
  input: { padding: '0.4rem 0.6rem', fontSize: '0.82rem', border: '1px solid #e5e7eb',
           borderRadius: '6px', background: '#fff', color: '#111', fontFamily: 'inherit' },
  chartWrap: { border: '1px solid #e5e7eb', borderRadius: '10px',
               padding: '1.25rem 0.5rem 0.5rem', backgroundColor: '#fafafa' },
  skeleton: { height: '320px', borderRadius: '10px', backgroundColor: '#f3f4f6' },
  tooltip: { border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '0.82rem',
             boxShadow: '0 4px 12px rgba(0,0,0,0.08)', backgroundColor: '#fff' },
  empty: { border: '1px solid #e5e7eb', borderRadius: '10px', padding: '2.5rem 1.5rem',
           backgroundColor: '#fafafa', textAlign: 'center', display: 'flex',
           flexDirection: 'column', alignItems: 'center', gap: '0.75rem' },
  emptyText: { fontSize: '0.85rem', color: '#666', margin: 0 },
  button: { padding: '0.45rem 1rem', fontSize: '0.82rem', border: 'none', borderRadius: '6px',
            background: '#111', color: '#fff', cursor: 'pointer', fontFamily: 'inherit' },
  error: { padding: '0.9rem 1.1rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca',
           borderRadius: '8px', fontSize: '0.83rem', color: '#b91c1c' },
}
