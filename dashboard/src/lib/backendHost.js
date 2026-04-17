export function getBackendHost() {
  if (import.meta.env.VITE_BACKEND_HOST) {
    return import.meta.env.VITE_BACKEND_HOST
  }

  const stored = localStorage.getItem('backendHost')
  if (stored) {
    return stored
  }

  return window.location.hostname
}

export function getApiBase() {
  return `http://${getBackendHost()}:8000`
}

export function getWsBase() {
  return `ws://${getBackendHost()}:8000`
}
