import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import Settings from './pages/Settings'
import { useWebSocket } from './hooks/useWebSocket'

const USER_ID = 'demo'

export default function App() {
  const { connected, latestData, scoreHistory, alerts } = useWebSocket(USER_ID)

  return (
    <BrowserRouter>
      <div className="app-layout">
        <nav className="navbar">
          <div className="navbar-brand">
            <div className="logo-icon">F</div>
            Flow State
          </div>

          <div className="navbar-nav">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              History
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Settings
            </NavLink>
          </div>

          <div className="navbar-status">
            <span className={`status-dot ${connected ? '' : 'disconnected'}`}></span>
            {connected ? 'Live' : 'Disconnected'}
          </div>
        </nav>

        <div className="page-container">
          <Routes>
            <Route path="/" element={
              <Dashboard
                userId={USER_ID}
                connected={connected}
                latestData={latestData}
                scoreHistory={scoreHistory}
                alerts={alerts}
              />
            } />
            <Route path="/history" element={<History userId={USER_ID} />} />
            <Route path="/settings" element={<Settings userId={USER_ID} />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
