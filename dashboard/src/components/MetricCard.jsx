import { motion } from 'framer-motion'

const TREND_ICONS = {
  up: String.fromCharCode(9650),     // triangle up
  down: String.fromCharCode(9660),   // triangle down
  neutral: String.fromCharCode(8212) // em dash
}

export default function MetricCard({ label, value, unit = '', trend = 'neutral', trendValue = '', icon = '', index = 0 }) {
  const trendClass = trend === 'up' ? 'up' : trend === 'down' ? 'down' : 'neutral'

  return (
    <motion.div
      className="metric-card"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <div className="metric-label">
        {icon && <span style={{ marginRight: '4px' }}>{icon}</span>}
        {label}
      </div>
      <div className="metric-value">
        {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(1)) : value}
        {unit && <span style={{ fontSize: '0.5em', color: '#666', marginLeft: '2px' }}>{unit}</span>}
      </div>
      {trendValue && (
        <div className={`metric-trend ${trendClass}`}>
          <span>{TREND_ICONS[trend] || TREND_ICONS.neutral}</span>
          {trendValue}
        </div>
      )}
    </motion.div>
  )
}
