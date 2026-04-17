import { useState } from 'react'
import { motion } from 'framer-motion'
import TrendChart from '../components/TrendChart'
import HeatmapGrid from '../components/HeatmapGrid'
import { useHistory, useHeatmap } from '../hooks/useScore'

const RANGES = [
  { key: '1h', label: '1H' },
  { key: '6h', label: '6H' },
  { key: '1d', label: '1D' },
  { key: '7d', label: '7D' },
  { key: '30d', label: '30D' },
]

export default function History({ userId }) {
  const [range, setRange] = useState('7d')
  const { history, loading } = useHistory(userId, range)
  const { heatmap } = useHeatmap(userId)

  // Compute stats from history
  const scores = history.map(h => h.score)
  const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
  const max = scores.length > 0 ? Math.max(...scores) : 0
  const min = scores.length > 0 ? Math.min(...scores) : 0

  const criticalCount = history.filter(h => h.severity === 'critical').length
  const highCount = history.filter(h => h.severity === 'high').length

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="history-header">
        <h1 className="history-title">History</h1>
        <div className="range-selector">
          {RANGES.map(r => (
            <button
              key={r.key}
              className={`range-btn ${range === r.key ? 'active' : ''}`}
              onClick={() => setRange(r.key)}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Row */}
      <div className="metric-cards-row" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="metric-card">
          <div className="metric-label">Average Score</div>
          <div className="metric-value" style={{ color: avg > 55 ? '#f97316' : '#4ade80' }}>
            {avg.toFixed(1)}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Peak Score</div>
          <div className="metric-value" style={{ color: max > 75 ? '#ef4444' : '#facc15' }}>
            {max.toFixed(1)}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Lowest</div>
          <div className="metric-value" style={{ color: '#4ade80' }}>
            {min.toFixed(1)}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Data Points</div>
          <div className="metric-value">{history.length}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Critical Events</div>
          <div className="metric-value" style={{ color: criticalCount > 0 ? '#ef4444' : '#666' }}>
            {criticalCount}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">High Events</div>
          <div className="metric-value" style={{ color: highCount > 0 ? '#f97316' : '#666' }}>
            {highCount}
          </div>
        </div>
      </div>

      {/* Main Trend Chart */}
      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="card-header">
          <span className="card-title">Score Over Time</span>
          <span className="card-badge" style={{ color: '#a0a0a0' }}>
            {loading ? 'Loading...' : `${history.length} points`}
          </span>
        </div>
        <TrendChart data={history} height={320} />
      </div>

      {/* Heatmap */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Burnout Patterns</span>
          <span className="card-badge" style={{ color: '#a0a0a0' }}>
            Day x Hour
          </span>
        </div>
        <HeatmapGrid data={heatmap} />
      </div>
    </motion.div>
  )
}
