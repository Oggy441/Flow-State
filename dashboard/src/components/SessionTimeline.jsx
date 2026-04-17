import { motion } from 'framer-motion'

export default function SessionTimeline({ data = [] }) {
  if (data.length === 0) {
    return (
      <div className="empty-state" style={{ minHeight: '60px' }}>
        <div className="empty-state-text">
          Session timeline will appear as data is collected.
        </div>
      </div>
    )
  }

  const SEVERITY_COLORS = {
    low: '#4ade80',
    moderate: '#facc15',
    high: '#f97316',
    critical: '#ef4444',
  }

  // Take last 60 data points for the mini timeline
  const points = data.slice(-60)
  const maxScore = 100
  const width = 100 // percentage
  const barWidth = width / Math.max(points.length, 1)

  return (
    <div style={{ width: '100%', padding: '8px 0' }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        height: '40px',
        gap: '1px',
        borderRadius: '4px',
        overflow: 'hidden',
      }}>
        {points.map((point, i) => {
          const height = Math.max((point.score / maxScore) * 100, 4)
          const color = SEVERITY_COLORS[point.severity] || '#4ade80'

          return (
            <motion.div
              key={i}
              initial={{ height: 0 }}
              animate={{ height: `${height}%` }}
              transition={{ delay: i * 0.01, duration: 0.2 }}
              style={{
                flex: 1,
                backgroundColor: color,
                borderRadius: '1px 1px 0 0',
                opacity: 0.7 + (i / points.length) * 0.3,
                minWidth: '2px',
              }}
            />
          )
        })}
      </div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '9px',
        color: '#666',
        marginTop: '4px',
      }}>
        <span>
          {points[0] && new Date(points[0].timestamp * 1000).toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit'
          })}
        </span>
        <span>
          {points[points.length - 1] && new Date(points[points.length - 1].timestamp * 1000).toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit'
          })}
        </span>
      </div>
    </div>
  )
}
