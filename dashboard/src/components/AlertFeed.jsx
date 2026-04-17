import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef } from 'react'

export default function AlertFeed({ alerts = [] }) {
  const feedRef = useRef(null)

  if (alerts.length === 0) {
    return (
      <div className="empty-state" style={{ minHeight: '200px' }}>
        <div className="empty-state-icon">...</div>
        <div className="empty-state-text">
          No alerts yet. Alerts will appear here when burnout indicators are detected.
        </div>
      </div>
    )
  }

  return (
    <div className="alert-feed" ref={feedRef}>
      <AnimatePresence initial={false}>
        {alerts.map((alert) => (
          <motion.div
            key={alert.id}
            className={`alert-item severity-${alert.severity}`}
            initial={{ opacity: 0, x: 20, height: 0 }}
            animate={{ opacity: 1, x: 0, height: 'auto' }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
          >
            <span className="alert-time">{alert.time}</span>
            <span className="alert-message">{alert.message}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
