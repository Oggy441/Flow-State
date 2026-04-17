import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const SEVERITY_COLORS = {
  low: '#4ade80',
  moderate: '#facc15',
  high: '#f97316',
  critical: '#ef4444',
}

function getSeverityFromScore(score) {
  if (score <= 30) return 'low'
  if (score <= 55) return 'moderate'
  if (score <= 75) return 'high'
  return 'critical'
}

export default function ScoreGauge({ score = 0, severity = 'low', label = '' }) {
  const [displayScore, setDisplayScore] = useState(0)
  const prevScore = useRef(0)

  // Animate the score number
  useEffect(() => {
    const start = prevScore.current
    const end = score
    const duration = 800
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = start + (end - start) * eased
      setDisplayScore(current)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
    prevScore.current = score
  }, [score])

  const actualSeverity = severity || getSeverityFromScore(score)
  const color = SEVERITY_COLORS[actualSeverity] || SEVERITY_COLORS.low

  // SVG arc calculations
  const size = 200
  const strokeWidth = 12
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const progress = displayScore / 100
  const dashOffset = circumference * (1 - progress * 0.75) // 270-degree arc
  const rotation = 135 // Start from bottom-left

  const isCritical = actualSeverity === 'critical'

  return (
    <div className="score-gauge-container">
      <motion.div
        className="score-gauge-svg"
        animate={isCritical ? {
          filter: [
            'drop-shadow(0 0 8px rgba(239,68,68,0.4))',
            'drop-shadow(0 0 20px rgba(239,68,68,0.7))',
            'drop-shadow(0 0 8px rgba(239,68,68,0.4))',
          ]
        } : {}}
        transition={isCritical ? { duration: 1.5, repeat: Infinity } : {}}
      >
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#2a2a2a"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
          />

          {/* Progress arc */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            strokeDashoffset={dashOffset}
            transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke 0.5s ease' }}
          />

          {/* Center text */}
          <text
            x={size / 2}
            y={size / 2 - 8}
            textAnchor="middle"
            dominantBaseline="middle"
            className="score-gauge-value"
            fill={color}
            style={{
              fontSize: '48px',
              fontWeight: 800,
              fontFamily: 'Inter, sans-serif',
            }}
          >
            {Math.round(displayScore)}
          </text>

          <text
            x={size / 2}
            y={size / 2 + 28}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#a0a0a0"
            style={{
              fontSize: '11px',
              fontWeight: 600,
              fontFamily: 'Inter, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            burnout score
          </text>
        </svg>
      </motion.div>

      <motion.div
        className="score-gauge-label"
        style={{ color }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        key={actualSeverity}
      >
        {actualSeverity.toUpperCase()}
      </motion.div>

      {label && (
        <div className="score-gauge-sublabel">{label}</div>
      )}
    </div>
  )
}
