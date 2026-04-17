import { useState } from 'react'
import { motion } from 'framer-motion'
import { getApiBase } from '../lib/backendHost'

const API_BASE = getApiBase()

export default function Settings({ userId }) {
  const [resetStatus, setResetStatus] = useState(null)

  const handleResetBaseline = async () => {
    if (!window.confirm('Reset your personal baseline? This will require recalibration.')) return

    try {
      const res = await fetch(`${API_BASE}/calibrate/reset?user_id=${userId}`, {
        method: 'POST',
      })
      const data = await res.json()
      setResetStatus(data.status === 'reset' ? 'Baseline reset successfully' : 'No baseline found')
      setTimeout(() => setResetStatus(null), 3000)
    } catch (err) {
      setResetStatus('Error resetting baseline')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      style={{ maxWidth: '700px' }}
    >
      <h1 className="history-title" style={{ marginBottom: 'var(--space-xl)' }}>Settings</h1>

      {/* Privacy Section */}
      <div className="settings-section">
        <h2 className="settings-section-title">Privacy & Data</h2>

        <div className="settings-row">
          <div>
            <div className="settings-label">Keystroke Content</div>
            <div className="settings-desc">No keystroke content is ever logged - only timing metadata</div>
          </div>
          <span className="card-badge" style={{
            backgroundColor: 'rgba(74, 222, 128, 0.15)',
            color: '#4ade80',
            padding: '4px 12px',
          }}>
            Protected
          </span>
        </div>

        <div className="settings-row">
          <div>
            <div className="settings-label">Data Processing</div>
            <div className="settings-desc">All processing happens on-device. Only aggregate feature vectors are analyzed.</div>
          </div>
          <span className="card-badge" style={{
            backgroundColor: 'rgba(74, 222, 128, 0.15)',
            color: '#4ade80',
            padding: '4px 12px',
          }}>
            Local
          </span>
        </div>

        <div className="settings-row">
          <div>
            <div className="settings-label">User Identity</div>
            <div className="settings-desc">Your ID is a local anonymous hash - no personal information is stored</div>
          </div>
          <code style={{
            fontSize: '12px',
            color: '#a0a0a0',
            background: '#1a1a1a',
            padding: '4px 8px',
            borderRadius: '4px',
          }}>
            {userId}
          </code>
        </div>
      </div>

      {/* Calibration Section */}
      <div className="settings-section">
        <h2 className="settings-section-title">Calibration</h2>

        <div className="settings-row">
          <div>
            <div className="settings-label">Personal Baseline</div>
            <div className="settings-desc">
              Your baseline is built from the first 50 data windows (~25 minutes).
              After calibration, all scores are computed as deviations from your personal norm.
            </div>
          </div>
          <button className="btn btn-danger" onClick={handleResetBaseline}>
            Reset Baseline
          </button>
        </div>

        {resetStatus && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: 'var(--space-md)',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--accent-amber)',
              marginTop: 'var(--space-md)',
            }}
          >
            {resetStatus}
          </motion.div>
        )}
      </div>

      {/* About Section */}
      <div className="settings-section">
        <h2 className="settings-section-title">About</h2>

        <div className="card" style={{ background: 'var(--bg-secondary)' }}>
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, marginBottom: 'var(--space-sm)' }}>
            Flow State v1.0
          </h3>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            Real-time burnout detection through behavioural biometrics. Flow State analyzes
            mouse movement patterns, typing dynamics, scroll behaviour, and session patterns
            to estimate cognitive fatigue without ever accessing your content.
          </p>
          <div style={{
            marginTop: 'var(--space-md)',
            paddingTop: 'var(--space-md)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-sm)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-muted)',
          }}>
            <div>Frontend: React 18 + Vite</div>
            <div>Backend: FastAPI + Python</div>
            <div>Charts: Recharts</div>
            <div>Storage: SQLite</div>
            <div>Real-time: WebSockets</div>
            <div>Animation: Framer Motion</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
