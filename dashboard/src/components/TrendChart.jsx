import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

const SEVERITY_BANDS = [
  { y: 30, label: 'Low', color: '#4ade80' },
  { y: 55, label: 'Moderate', color: '#facc15' },
  { y: 75, label: 'High', color: '#f97316' },
]

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  const data = payload[0].payload
  const score = data.score
  let severity = 'low'
  if (score > 75) severity = 'critical'
  else if (score > 55) severity = 'high'
  else if (score > 30) severity = 'moderate'

  const COLORS = {
    low: '#4ade80',
    moderate: '#facc15',
    high: '#f97316',
    critical: '#ef4444',
  }

  return (
    <div style={{
      background: '#2d2d2d',
      border: '1px solid #3a3a3a',
      borderRadius: '8px',
      padding: '10px 14px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
    }}>
      <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>
        {data.timeLabel || label}
      </div>
      <div style={{ fontSize: '20px', fontWeight: 700, color: COLORS[severity] }}>
        {score.toFixed(1)}
      </div>
      <div style={{ fontSize: '10px', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {severity}
      </div>
    </div>
  )
}

export default function TrendChart({ data = [], height = 220 }) {
  // Format timestamps for display
  const chartData = data.map((d, i) => {
    const date = new Date(d.timestamp * 1000)
    return {
      ...d,
      index: i,
      timeLabel: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      dateLabel: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }
  })

  if (chartData.length === 0) {
    return (
      <div className="empty-state" style={{ height }}>
        <div className="empty-state-icon">~</div>
        <div className="empty-state-text">
          No trend data yet. Start the simulator to see score trends appear here.
        </div>
      </div>
    )
  }

  // Compute gradient ID based on latest score
  const latestScore = chartData[chartData.length - 1]?.score || 0
  let gradientColor = '#4ade80'
  if (latestScore > 75) gradientColor = '#ef4444'
  else if (latestScore > 55) gradientColor = '#f97316'
  else if (latestScore > 30) gradientColor = '#facc15'

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
        <defs>
          <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={gradientColor} stopOpacity={0.3} />
            <stop offset="95%" stopColor={gradientColor} stopOpacity={0.02} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />

        <XAxis
          dataKey="timeLabel"
          tick={{ fontSize: 10, fill: '#666' }}
          axisLine={{ stroke: '#2a2a2a' }}
          tickLine={false}
          interval="preserveStartEnd"
        />

        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: '#666' }}
          axisLine={{ stroke: '#2a2a2a' }}
          tickLine={false}
          ticks={[0, 25, 50, 75, 100]}
        />

        {SEVERITY_BANDS.map(band => (
          <ReferenceLine
            key={band.y}
            y={band.y}
            stroke={band.color}
            strokeDasharray="4 4"
            strokeOpacity={0.3}
          />
        ))}

        <Tooltip content={<CustomTooltip />} />

        <Area
          type="monotone"
          dataKey="score"
          stroke={gradientColor}
          strokeWidth={2}
          fill="url(#scoreGradient)"
          animationDuration={500}
          dot={false}
          activeDot={{ r: 4, stroke: gradientColor, strokeWidth: 2, fill: '#1a1a1a' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
