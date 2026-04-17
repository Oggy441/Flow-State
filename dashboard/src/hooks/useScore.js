import { useState, useEffect, useCallback } from 'react'
import { getApiBase } from '../lib/backendHost'

const API_BASE = getApiBase()

export function useScore(userId) {
  const [score, setScore] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchScore = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/score/${userId}`)
      const data = await res.json()
      setScore(data)
    } catch (err) {
      console.warn('Score fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchScore()
    const interval = setInterval(fetchScore, 10000) // poll every 10s as fallback
    return () => clearInterval(interval)
  }, [fetchScore])

  return { score, loading, refetch: fetchScore }
}

export function useHistory(userId, range = '7d') {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/history/${userId}?range=${range}`)
      const data = await res.json()
      setHistory(data)
    } catch (err) {
      console.warn('History fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [userId, range])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  return { history, loading, refetch: fetchHistory }
}

export function useHeatmap(userId) {
  const [heatmap, setHeatmap] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchHeatmap = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/heatmap/${userId}`)
      const data = await res.json()
      setHeatmap(data.heatmap || [])
    } catch (err) {
      console.warn('Heatmap fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchHeatmap()
    const interval = setInterval(fetchHeatmap, 30000)
    return () => clearInterval(interval)
  }, [fetchHeatmap])

  return { heatmap, loading, refetch: fetchHeatmap }
}
