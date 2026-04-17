import { useState } from 'react'
import { motion } from 'framer-motion'

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const HOURS = Array.from({ length: 24 }, (_, i) => i)

function getHeatColor(score) {
  if (score <= 0) return '#1a1a1a'
  if (score <= 20) return '#1a3a2a'
  if (score <= 30) return '#2a5a3a'
  if (score <= 40) return '#4a6a2a'
  if (score <= 55) return '#6a6a1a'
  if (score <= 65) return '#8a5a1a'
  if (score <= 75) return '#aa4a1a'
  if (score <= 85) return '#ba3020'
  return '#d01a1a'
}

export default function HeatmapGrid({ data = [] }) {
  const [tooltip, setTooltip] = useState(null)

  // Index data by day-hour
  const grid = {}
  data.forEach(cell => {
    grid[`${cell.day}-${cell.hour}`] = cell
  })

  const handleCellHover = (e, day, hour) => {
    const cell = grid[`${day}-${hour}`]
    const rect = e.target.getBoundingClientRect()
    setTooltip({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      day: DAYS[day],
      hour: `${hour}:00`,
      score: cell?.score || 0,
      count: cell?.count || 0,
    })
  }

  if (data.length === 0) {
    return (
      <div className="empty-state" style={{ minHeight: '150px' }}>
        <div className="empty-state-icon">#</div>
        <div className="empty-state-text">
          Heatmap data will populate as more sessions are recorded over different days and hours.
        </div>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative' }}>
      {/* Hour labels */}
      <div className="heatmap-hour-labels">
        <div></div>
        {HOURS.map(h => (
          <div key={h} className="heatmap-hour-label">
            {h % 3 === 0 ? `${h}` : ''}
          </div>
        ))}
      </div>

      {/* Grid */}
      {DAYS.map((dayName, dayIdx) => (
        <div className="heatmap-grid" key={dayIdx}>
          <div className="heatmap-label">{dayName}</div>
          {HOURS.map(hour => {
            const cell = grid[`${dayIdx}-${hour}`]
            const score = cell?.score || 0

            return (
              <motion.div
                key={hour}
                className="heatmap-cell"
                style={{ backgroundColor: getHeatColor(score) }}
                onMouseEnter={(e) => handleCellHover(e, dayIdx, hour)}
                onMouseLeave={() => setTooltip(null)}
                whileHover={{ scale: 1.4 }}
                transition={{ duration: 0.1 }}
              />
            )
          })}
        </div>
      ))}

      {/* Legend */}
      <div className="heatmap-legend">
        <span>Low</span>
        <div className="heatmap-legend-gradient"></div>
        <span>Critical</span>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="tooltip"
          style={{
            position: 'fixed',
            left: tooltip.x,
            top: tooltip.y,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <strong>{tooltip.day} {tooltip.hour}</strong>
          <br />
          Score: {tooltip.score.toFixed(1)} ({tooltip.count} samples)
        </div>
      )}
    </div>
  )
}
