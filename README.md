# 🔥 BurnoutRadar

BurnoutRadar is a real-time burnout detection system using behavioural biometrics. It monitors mouse movements, typing dynamics, and session patterns to estimate cognitive fatigue without accessing actual keystroke content.

## Setup and Running

The project requires running three separate processes: the backend server, the frontend dashboard, and the data simulator (which acts as the user tracking agent for demo purposes).

### Prerequisites

Ensure you have the following installed on your machine:
- Node.js (v16+ recommended)
- Python (3.9+ recommended)

---

### Step 1: Start the Backend Server

The backend is built with FastAPI and handles data ingestion, feature extraction, burnout scoring, and WebSocket connections.

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd burnout-radar/backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   *The API will be available at `http://localhost:8000`.*

---

### Step 2: Start the Frontend Dashboard

The dashboard is built with React and Vite. It consumes the API and WebSocket feeds to visualize the data.

1. Open a **new** terminal window and navigate to the `dashboard` folder:
   ```bash
   cd burnout-radar/dashboard
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The dashboard will be available at `http://localhost:5173`.*

---

### Step 3: Run the Data Simulator

To see live data flowing into the dashboard, you need to run the agent simulator, which generates synthetic tracking events.

1. Open a **new** (third) terminal window and navigate to the `agent` folder:
   ```bash
   cd burnout-radar/agent
   ```
2. Run the simulator script in a specific scenario. For a demo that gradually builds up from normal to crisis (burnout), use the `ramp` scenario:
   ```bash
   python simulate.py --user demo --scenario ramp --duration 300 --interval 3
   ```

#### Simulator Options:

- `--scenario`: The type of data to generate.
  - `normal` (15-30 score, stable patterns)
  - `fatigue` (40-55 score, slowing down)
  - `burnout` (65-85 score, erratic behavior)
  - `crisis` (85-100 score, near-zero productivity)
  - `ramp` (Gradually transitions from normal to crisis over the duration)
- `--duration`: Total simulation time in seconds.
- `--interval`: Seconds between each synthetic payload (default is 3s).

### Demo Experience

Once everything is running, open the dashboard in your browser. Leave it open while the simulator pushes data. You will see the score gauge react, trends plot out, alerts trigger as patterns worsen, and recommendations adapt to the simulated behavior.
