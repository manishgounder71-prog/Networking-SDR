import { useState, useEffect } from 'react'
import './index.css'

const API_BASE = 'http://localhost:8000'

const STEPS = [
  { id: 'memory',      icon: '🧠', label: 'Memory Scan',   desc: 'Checking history...' },
  { id: 'research',    icon: '🔍', label: 'Intelligence',  desc: 'News & Funding...' },
  { id: 'suggestions', icon: '✨', label: 'Agent Strategy', desc: 'Generating...' },
  { id: 'storing',     icon: '💾', label: 'CRM Sync',       desc: 'Saving...' },
]

const SENTIMENT_CONFIG = {
  Bullish:  { color: '#fff',  bg: '#1a1a1a', border: '#555', icon: '▲' },
  Neutral:  { color: '#888',  bg: '#111',    border: '#333', icon: '●' },
  Bearish:  { color: '#444',  bg: '#0d0d0d', border: '#222', icon: '▼' },
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusTag({ label, active, provider }) {
  return (
    <div className={`status-tag ${active ? 'active' : ''}`}>
      <span className="dot" style={{ background: active ? '#fff' : '#444' }} />
      <span>{label}: {provider}</span>
    </div>
  )
}

function PipelineView({ currentStep, done }) {
  return (
    <div className="pipeline-view">
      <div className="report-section-title">Workflow Execution</div>
      {STEPS.map((step, i) => {
        const stepIdx = STEPS.findIndex(s => s.id === currentStep)
        const isActive = step.id === currentStep
        const isDone   = done || (stepIdx > i)
        return (
          <div key={step.id} className={`pipe-step ${isActive ? 'active' : ''}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div className="step-icon">{isDone ? '●' : step.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: isDone ? 'var(--text-vibrant)' : 'var(--text-main)' }}>
                  {step.label}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  {isActive ? 'Processing Neural Data...' : isDone ? 'Completed' : step.desc}
                </div>
              </div>
              {isActive && <div className="spinner-ag" />}
            </div>
          </div>
        )
      })}
    </div>
  )
}

/** Circular SVG gauge for lead score */
function ScoreMeter({ score = 0 }) {
  const R = 32
  const C = 2 * Math.PI * R
  const pct = Math.min(Math.max(score, 0), 100)
  const dashoffset = C - (pct / 100) * C

  // Color based on score range (monochrome + accent)
  const color = pct >= 75 ? '#fff' : pct >= 45 ? '#888' : '#444'

  return (
    <div className="score-meter" title={`Lead Score: ${score}/100`}>
      <svg width="84" height="84" viewBox="0 0 84 84">
        {/* Track */}
        <circle cx="42" cy="42" r={R} fill="none" stroke="#1c1c1c" strokeWidth="6" />
        {/* Progress */}
        <circle
          cx="42" cy="42" r={R}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={dashoffset}
          transform="rotate(-90 42 42)"
          style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }}
        />
      </svg>
      <div className="score-value">
        <span style={{ fontSize: 18, fontWeight: 900, color, fontFamily: 'Space Grotesk' }}>{pct}</span>
        <span style={{ fontSize: 9, color: '#444', fontWeight: 800 }}>/ 100</span>
      </div>
      <div style={{ fontSize: 9, color: '#555', fontWeight: 800, textAlign: 'center', marginTop: 6, letterSpacing: 2 }}>LEAD SCORE</div>
    </div>
  )
}

/** Sentiment badge with icon */
function SentimentBadge({ sentiment = 'Neutral' }) {
  const cfg = SENTIMENT_CONFIG[sentiment] || SENTIMENT_CONFIG.Neutral
  return (
    <div
      className="sentiment-badge"
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}
    >
      <span style={{ fontSize: 10, marginRight: 6 }}>{cfg.icon}</span>
      <span>{sentiment.toUpperCase()}</span>
    </div>
  )
}

/** Session analytics computed from history */
function SessionAnalytics({ history }) {
  if (!history.length) return null

  const totalLeads = history.length
  const scores = history.map(h => Number(h.score || h.suggestions?.score || 0)).filter(Boolean)
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : '–'

  const sentimentCounts = history.reduce((acc, h) => {
    const s = h.sentiment || h.suggestions?.sentiment || 'Neutral'
    acc[s] = (acc[s] || 0) + 1
    return acc
  }, {})

  return (
    <div className="analytics-panel">
      <div className="analytics-title">SESSION ANALYTICS</div>
      <div className="analytics-row">
        <span className="analytics-label">Total Leads</span>
        <span className="analytics-value">{totalLeads}</span>
      </div>
      <div className="analytics-row">
        <span className="analytics-label">Avg Score</span>
        <span className="analytics-value">{avgScore}</span>
      </div>
      {Object.entries(sentimentCounts).map(([sent, count]) => {
        const cfg = SENTIMENT_CONFIG[sent] || SENTIMENT_CONFIG.Neutral
        return (
          <div key={sent} className="analytics-row">
            <span className="analytics-label" style={{ color: cfg.color }}>{cfg.icon} {sent}</span>
            <span className="analytics-value">{count}</span>
          </div>
        )
      })}
    </div>
  )
}

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [form, setForm]       = useState({ name: '', company: '', linkedin_url: '', notes: '' })
  const [loading, setLoading] = useState(false)
  const [currentStep, setStep]= useState(null)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const [history, setHistory] = useState([])
  const [status, setStatus]   = useState(null)
  const [copied, setCopied]   = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [leadsRes, statusRes] = await Promise.all([
        fetch(`${API_BASE}/leads`).then(r => r.json()),
        fetch(`${API_BASE}/status`).then(r => r.json())
      ])
      const sortedLeads = (leadsRes.leads || []).sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
      setHistory(sortedLeads)
      setStatus(statusRes)
    } catch {
      console.warn('Backend offline. Reconnecting...')
    }
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms))

  const handleSubmit = async e => {
    e.preventDefault()
    if (!form.name && !form.company) return
    setLoading(true); setError(null); setResult(null)

    const animateSteps = async () => {
      for (const step of STEPS) {
        setStep(step.id)
        await sleep(800)
      }
    }

    try {
      const runner = fetch(`${API_BASE}/process-lead`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      }).then(r => r.json())

      const [data] = await Promise.all([runner, animateSteps()])
      setResult(data)
      fetchData()
    } catch {
      setError('API Offline. Please check backend server.')
    } finally {
      setLoading(false); setStep(null)
    }
  }

  const handleDelete = async (e, lead) => {
    e.stopPropagation()
    if (!confirm(`Delete ${lead.name}?`)) return
    await fetch(`${API_BASE}/leads?name=${encodeURIComponent(lead.name)}&company=${encodeURIComponent(lead.company || '')}`, { method: 'DELETE' })
    fetchData()
    if (result && (result.lead_name === lead.name || result.name === lead.name)) setResult(null)
  }

  const copyToClipboard = () => {
    const s = result.suggestions
    const text = `Subject: ${s.subject}\n\n${s.opener}\n\n${s.value_prop}\n\nCTA: ${s.call_to_action}`
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const openLinkedIn = () => {
    const name = result?.lead_name || result?.name || ''
    const company = result?.company || ''
    const query = encodeURIComponent(`${name} ${company}`.trim())
    window.open(`https://www.linkedin.com/search/results/people/?keywords=${query}`, '_blank')
  }
  
  const fillDemo = () => {
    setForm({
      name: 'Jensen Huang',
      company: 'Nvidia',
      linkedin_url: '',
      notes: 'Strategic interest in AI data centers.'
    })
  }

  // Extract score/sentiment from result (handle both direct and nested structures)
  const score     = result?.suggestions?.score     ?? result?.score     ?? null
  const sentiment = result?.suggestions?.sentiment ?? result?.sentiment ?? null

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-row">
            <span className="brand-icon">⊡</span>
            <span className="brand-name">NETWORK SDR</span>
          </div>
        </div>

        <div className="sidebar-title">Intelligence Log</div>
        <div className="history-list">
          {history.length === 0 && <div style={{ padding: 12, fontSize: 12, color: '#444' }}>No recent leads</div>}
          {history.map((h, i) => (
            <div
              key={i}
              className={`history-item ${result?.lead_name === h.name || result?.name === h.name ? 'active' : ''}`}
              onClick={() => setResult(h)}
            >
              <button className="h-delete-btn" style={{ color: '#555' }} onClick={(e) => handleDelete(e, h)}>discard</button>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-vibrant)' }}>{h.name}</div>
              <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between', gap: 8, marginTop: 4 }}>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: 1, flex: 1 }}>{h.company || 'Private'}</div>
                {(h.score || h.suggestions?.score) && (
                  <span style={{ fontSize: 9, background: '#1a1a1a', color: '#888', padding: '2px 6px', borderRadius: 2, fontWeight: 800, border: '1px solid #2a2a2a' }}>
                    {h.score || h.suggestions?.score}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Session Analytics */}
        <SessionAnalytics history={history} />

        {/* Status Tags */}
        <div style={{ marginTop: 'auto', padding: '20px 0', borderTop: '1px solid #1a1a1a' }}>
          {status && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <StatusTag label="AI ENGINE" active={status.ai?.openai_enabled || status.ai?.lyzr_enabled} provider={status.ai?.lyzr_enabled ? 'LYZR' : status.ai?.openai_enabled ? 'OPENAI' : 'HEURISTIC'} />
              <StatusTag label="DATA SYNC"  active={status.storage?.connected} provider="SHEETS" />
              <StatusTag label="RESEARCH"   active={status.research?.connected} provider={status.research?.provider || 'FALLBACK'} />
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-container">

          {/* Header */}
          <header style={{ marginBottom: 48 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 10, fontWeight: 800, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 12 }}>
              Standard Operating Procedure: Lead Acquisition
            </div>
            <h1 style={{ fontFamily: 'Space Grotesk', fontSize: 44, color: 'var(--text-vibrant)', letterSpacing: -1 }}>
              Intelligence <span style={{ color: 'var(--text-muted)' }}>Command</span>
            </h1>
          </header>

          {/* Command Bar */}
          <div className="command-center ag-card">
            <form onSubmit={handleSubmit}>
              <div className="search-grid">
                <div className="input-wrapper">
                  <label>Full Name</label>
                  <input className="ag-input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Satya Nadella" />
                </div>
                <div className="input-wrapper">
                  <label>Company Domain</label>
                  <input className="ag-input" value={form.company} onChange={e => setForm({...form, company: e.target.value})} placeholder="e.g. Microsoft" />
                </div>
              </div>
              {error && <div style={{ color: 'var(--accent-error)', fontSize: 12, marginBottom: 16, fontWeight: 700 }}>EXC: {error}</div>}
              <div style={{ display: 'flex', gap: 12 }}>
                <button type="submit" className="btn-primary" style={{ flex: 2 }} disabled={loading}>
                  {loading ? 'Processing Neural Data...' : 'Execute Analysis'}
                </button>
                <button type="button" className="btn-secondary" style={{ flex: 1 }} onClick={fillDemo} disabled={loading}>
                  Demo Mode
                </button>
              </div>
            </form>
          </div>

          {/* Pipeline Progress */}
          {loading && (
            <div className="ag-card" style={{ marginBottom: 40, borderLeft: '4px solid #333' }}>
              <PipelineView currentStep={currentStep} done={false} />
            </div>
          )}

          {/* Intelligence Report */}
          {result && !loading && (
            <div className="report-grid">
              <div className="ag-card" style={{ borderLeft: '4px solid #fff' }}>

                {/* Report Header */}
                <div className="report-header">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 24 }}>

                    {/* Name & Company */}
                    <div style={{ flex: 1 }}>
                      <h2 className="report-lead-name">{result.lead_name || result.name}</h2>
                      <div style={{ color: 'var(--text-dim)', fontSize: 14, fontWeight: 600, textTransform: 'uppercase', marginBottom: 16 }}>{result.company}</div>

                      {/* Tags row */}
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {(result.suggestions?.tags || result.tags || []).map((t, i) => (
                          <span key={i} style={{ fontSize: 9, background: '#222', padding: '4px 10px', borderRadius: 2, color: '#999', fontWeight: 800, border: '1px solid #333' }}>
                            {t.toUpperCase()}
                          </span>
                        ))}
                      </div>

                      {/* Action Row — LinkedIn + Status badge */}
                      <div style={{ display: 'flex', gap: 12, marginTop: 20, alignItems: 'center' }}>
                        <button className="btn-linkedin" onClick={openLinkedIn} title="Find on LinkedIn">
                          <span style={{ marginRight: 6, fontSize: 12 }}>in</span> Find on LinkedIn
                        </button>
                        <div className="status-tag active">
                          {result.is_returning ? 'EXISTING RECORD' : 'NEW ACQUISITION'}
                        </div>
                      </div>
                    </div>

                    {/* Score Meter + Sentiment */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, minWidth: 100 }}>
                      {score !== null && <ScoreMeter score={score} />}
                      {sentiment && <SentimentBadge sentiment={sentiment} />}
                    </div>
                  </div>
                </div>

                {/* Two-column report body */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48, marginTop: 32 }}>

                  {/* Briefing / Research */}
                  <div>
                    <div className="report-section-title">Briefing Report</div>
                    {(result.research?.articles || []).slice(0, 3).map((a, i) => (
                      <div key={i} style={{ marginBottom: 20 }}>
                        <a href={a.link || '#'} target="_blank" rel="noreferrer" style={{ fontWeight: 700, color: 'var(--text-vibrant)', fontSize: 14, marginBottom: 4, display: 'block', textDecoration: 'none' }}>
                          {a.title}
                          {a.link && <span style={{ fontSize: 9, marginLeft: 6, color: '#444' }}>↗</span>}
                        </a>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{a.source} • {a.date}</div>
                      </div>
                    ))}
                    {(!result.research?.articles || result.research.articles.length === 0) && (
                      <div style={{ color: '#444', fontSize: 12 }}>No public records available for this cycle.</div>
                    )}
                  </div>

                  {/* Outreach Strategy */}
                  <div>
                    <div className="report-section-title">Strategic Directive</div>
                    <div className="outreach-box">
                      <div style={{ fontSize: 9, color: '#555', fontWeight: 800, marginBottom: 8 }}>SUBJECT LINE</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 24 }}>{result.suggestions?.subject}</div>

                      <div style={{ fontSize: 9, color: '#555', fontWeight: 800, marginBottom: 8 }}>OPENING VECTOR</div>
                      <div style={{ fontSize: 13, color: '#bbb', marginBottom: 24, fontStyle: 'italic' }}>"{result.suggestions?.opener}"</div>

                      <div style={{ fontSize: 9, color: '#555', fontWeight: 800, marginBottom: 8 }}>PRIMARY VALUE PROP</div>
                      <div style={{ fontSize: 13, color: '#bbb', marginBottom: 32 }}>{result.suggestions?.value_prop}</div>

                      <button onClick={copyToClipboard} className={`btn-copy ${copied ? 'copied' : ''}`}>
                        {copied ? '✓ DIRECTIVE COPIED' : 'COPY DIRECTIVE'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div style={{ marginTop: 48, paddingTop: 32, borderTop: '1px solid #1a1a1a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 700 }}>
                    SYSTEM: RECORD PERSISTED TO {status?.storage?.backend?.toUpperCase() || 'LOCAL CACHE'}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--accent-success)', fontWeight: 800 }}>READY</div>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!result && !loading && (
            <div className="ag-card" style={{ textAlign: 'center', padding: '120px 40px', background: 'transparent', borderStyle: 'dashed' }}>
              <div style={{ fontSize: 32, marginBottom: 24, opacity: 0.1 }}>⊡</div>
              <h3 style={{ color: 'var(--text-vibrant)', fontSize: 14, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 2 }}>Awaiting Input</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 8 }}>Initiate sequence by providing target coordinates above.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  )
}
