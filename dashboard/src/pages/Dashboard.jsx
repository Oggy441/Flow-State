import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import ScoreGauge from '../components/ScoreGauge'
import TrendChart from '../components/TrendChart'
import MetricCard from '../components/MetricCard'
import AlertFeed from '../components/AlertFeed'
import HeatmapGrid from '../components/HeatmapGrid'
import RecoPanel from '../components/RecoPanel'
import SessionTimeline from '../components/SessionTimeline'
import { useHeatmap } from '../hooks/useScore'

export default function Dashboard({ userId, connected, latestData, scoreHistory, alerts }) {
  const { heatmap } = useHeatmap(userId)

  const data = latestData
  const score = data?.score || 0
  const severity = data?.severity || 'low'
  const factors = data?.factors || []
  const calibrationReady = data?.calibration_ready || false
  const sampleCount = data?.sample_count || 0

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Main dashboard grid — restructured for better alignment */}
      <div className="dashboard-grid">

        {/* Left: Score Gauge */}
        <div className="score-section card">
          <div className="card-header">
            <span className="card-title">Live Score</span>
            <span
              className="card-badge"
              style={{
                backgroundColor: `${data?.color || '#4ade80'}22`,
                color: data?.color || '#4ade80',
              }}
            >
              {connected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <ScoreGauge
            score={score}
            severity={severity}
            label={calibrationReady ? 'Calibrated' : `Calibrating ${sampleCount}/50`}
          />

          {/* Mini metrics under gauge */}
          <div className="gauge-mini-stats">
            <div className="gauge-mini-stat">
              <span className="gauge-mini-label">Events</span>
              <span className="gauge-mini-value">{sampleCount}</span>
            </div>
            <div className="gauge-mini-stat">
              <span className="gauge-mini-label">Alerts</span>
              <span className="gauge-mini-value">{alerts.length}</span>
            </div>
            <div className="gauge-mini-stat">
              <span className="gauge-mini-label">Session</span>
              <span className="gauge-mini-value">{Math.round(scoreHistory.length * 30 / 60)}m</span>
            </div>
          </div>
        </div>

        {/* Center: Trend + Metrics stacked */}
        <div className="center-section">
          <div className="card" style={{ marginBottom: 'var(--space-md)' }}>
            <div className="card-header">
              <span className="card-title">Score Trend</span>
              <span className="card-badge" style={{ color: '#a0a0a0' }}>
                {scoreHistory.length} points
              </span>
            </div>
            <TrendChart data={scoreHistory} height={180} />
          </div>

          {/* Session Timeline */}
          <div className="card" style={{ marginBottom: 'var(--space-md)' }}>
            <div className="card-header">
              <span className="card-title">Session Timeline</span>
            </div>
            <SessionTimeline data={scoreHistory} />
          </div>

          {/* Factor Metric Cards — always show raw values from metrics payload */}
          <div className="factor-metrics-grid">
            <MetricCard
              label="WPM"
              value={data?.metrics?.wpm ?? 0}
              unit="wpm"
              trend={data?.metrics?.wpm > 0 && data?.metrics?.wpm < 25 ? 'up' : 'neutral'}
              trendValue={data?.metrics?.wpm > 0 && data?.metrics?.wpm < 25 ? 'Slow' : data?.metrics?.wpm >= 25 ? 'Normal' : 'Idle'}
              index={0}
            />
            <MetricCard
              label="Mouse Speed"
              value={Math.round(data?.metrics?.mouse_speed ?? 0)}
              unit="px/s"
              trend={data?.metrics?.mouse_speed > 600 ? 'up' : 'neutral'}
              trendValue={data?.metrics?.mouse_speed > 600 ? 'Fast' : 'Normal'}
              index={1}
            />
            <MetricCard
              label="Mouse Jitter"
              value={Math.round(data?.metrics?.mouse_jitter ?? 0)}
              unit="°"
              trend={data?.metrics?.mouse_jitter > 30 ? 'up' : 'neutral'}
              trendValue={data?.metrics?.mouse_jitter > 30 ? 'Elevated' : 'Stable'}
              index={2}
            />
            <MetricCard
              label="Idle"
              value={Math.round(data?.metrics?.idle_sec ?? 0)}
              unit="s"
              trend={data?.metrics?.idle_sec > 20 ? 'up' : 'neutral'}
              trendValue={data?.metrics?.idle_sec > 20 ? 'High' : 'Active'}
              index={3}
            />
            <MetricCard
              label="Error Rate"
              value={Math.round((data?.metrics?.backspace_rate ?? 0) * 100)}
              unit="%"
              trend={(data?.metrics?.backspace_rate ?? 0) > 0.15 ? 'up' : 'neutral'}
              trendValue={(data?.metrics?.backspace_rate ?? 0) > 0.15 ? 'Rising' : 'Normal'}
              index={4}
            />
            <MetricCard
              label="Clicks"
              value={data?.metrics?.clicks ?? 0}
              unit=""
              trend="neutral"
              trendValue={(data?.metrics?.clicks ?? 0) > 0 ? 'Active' : 'None'}
              index={5}
            />
          </div>
        </div>

        {/* Right: Alerts */}
        <div className="alerts-section card">
          <div className="card-header">
            <span className="card-title">Alerts</span>
            <span className="card-badge" style={{
              backgroundColor: alerts.length > 0 ? 'rgba(233,69,96,0.15)' : 'transparent',
              color: alerts.length > 0 ? '#e94560' : '#666',
            }}>
              {alerts.length}
            </span>
          </div>
          <AlertFeed alerts={alerts} />
        </div>

        {/* Full width: Heatmap */}
        <div className="heatmap-section card">
          <div className="card-header">
            <span className="card-title">Activity Heatmap</span>
            <span className="card-badge" style={{ color: '#a0a0a0' }}>
              Day x Hour
            </span>
          </div>
          <HeatmapGrid data={heatmap} />
        </div>

        {/* Full width: Recommendations */}
        <div className="reco-section card">
          <div className="card-header">
            <span className="card-title">Recommendations</span>
          </div>
          <RecoPanel score={score} factors={factors} />
        </div>
      </div>
    </motion.div>
  )
}
