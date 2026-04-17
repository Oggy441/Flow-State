import { useState, useEffect, useRef, useCallback } from 'react'
import { getWsBase } from '../lib/backendHost'

const WS_BASE = getWsBase()
const RECONNECT_DELAY = 3000
const MAX_HISTORY = 200

export function useWebSocket(userId) {
  const [connected, setConnected] = useState(false)
  const [latestData, setLatestData] = useState(null)
  const [scoreHistory, setScoreHistory] = useState([])
  const [alerts, setAlerts] = useState([])
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(`${WS_BASE}/ws/${userId}`)

    ws.onopen = () => {
      setConnected(true)
      console.log('[WS] Connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'pong') return

        setLatestData(data)

        // Append to score history
        setScoreHistory(prev => {
          const next = [...prev, {
            timestamp: data.timestamp,
            score: data.score,
            severity: data.severity,
          }]
          return next.slice(-MAX_HISTORY)
        })

        // Generate alerts from factors
        if (data.factors && data.factors.length > 0) {
          const ts = new Date(data.timestamp * 1000)
          const timeStr = ts.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

          const newAlerts = data.factors.map((f, i) => ({
            id: `${data.timestamp}-${i}`,
            time: timeStr,
            message: f.message,
            severity: data.severity,
          }))

          setAlerts(prev => [...newAlerts, ...prev].slice(0, 50))
        }
      } catch (err) {
        console.warn('[WS] Parse error:', err)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('[WS] Disconnected, reconnecting...')
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }

    ws.onerror = (err) => {
      console.warn('[WS] Error:', err)
      ws.close()
    }

    wsRef.current = ws
  }, [userId])

  useEffect(() => {
    connect()

    // Ping to keep alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected, latestData, scoreHistory, alerts }
}
