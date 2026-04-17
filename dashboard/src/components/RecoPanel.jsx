import { motion } from 'framer-motion'

const RULES = [
  {
    condition: (score, factors, hour) => score > 60 && hour >= 21,
    icon: String.fromCharCode(127769), // moon
    title: 'Time to wind down',
    desc: 'Your burnout score is elevated and it\'s getting late. Consider wrapping up for the day.',
    priority: 1,
  },
  {
    condition: (score, factors) => factors.some(f => f.factor === 'backspace_zscore'),
    icon: String.fromCharCode(9888),  // warning
    title: 'Error rate is climbing',
    desc: 'You\'re making more corrections than usual. A short break could help restore focus.',
    priority: 2,
  },
  {
    condition: (score, factors) => factors.some(f => f.factor === 'idle_ratio' && f.value < 0.05),
    icon: String.fromCharCode(9749),  // coffee
    title: 'You haven\'t paused recently',
    desc: 'Continuous work without breaks accelerates fatigue. Try a 5-minute walk.',
    priority: 2,
  },
  {
    condition: (score, factors) => factors.some(f => f.factor === 'task_switch_rate'),
    icon: String.fromCharCode(128256), // shuffle
    title: 'High context switching',
    desc: 'Frequent task switches fragment your attention. Try focusing on one task for 25 minutes.',
    priority: 3,
  },
  {
    condition: (score, factors) => factors.some(f => f.factor === 'mouse_jitter_zscore'),
    icon: String.fromCharCode(128075), // waving hand
    title: 'Physical tension detected',
    desc: 'Erratic mouse movement may indicate stress. Try some hand stretches.',
    priority: 3,
  },
  {
    condition: (score) => score > 70,
    icon: String.fromCharCode(128161), // light bulb
    title: 'Burnout risk is high',
    desc: 'Multiple indicators suggest significant fatigue. Consider taking a longer break or finishing for the day.',
    priority: 1,
  },
  {
    condition: (score) => score <= 30,
    icon: String.fromCharCode(10004), // check mark
    title: 'You\'re in good shape',
    desc: 'Your patterns look healthy. Keep maintaining this pace.',
    priority: 5,
  },
]

export default function RecoPanel({ score = 0, factors = [], hour = new Date().getHours() }) {
  const activeRecos = RULES
    .filter(rule => rule.condition(score, factors, hour))
    .sort((a, b) => a.priority - b.priority)
    .slice(0, 4)

  if (activeRecos.length === 0) {
    return (
      <div className="empty-state" style={{ minHeight: '80px' }}>
        <div className="empty-state-text">
          Recommendations will appear based on your current burnout indicators.
        </div>
      </div>
    )
  }

  return (
    <div className="reco-list">
      {activeRecos.map((reco, i) => (
        <motion.div
          key={i}
          className="reco-item"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, duration: 0.3 }}
        >
          <div className="reco-icon">{reco.icon}</div>
          <div className="reco-content">
            <div className="reco-title">{reco.title}</div>
            <div className="reco-desc">{reco.desc}</div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
