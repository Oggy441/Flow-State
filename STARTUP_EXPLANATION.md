# BurnoutRadar Startup Guide and Code Explanation

This document contains exactly what is in the main `README.md` file, but interjects with detailed, visible explanations for what every single instruction, command, and step actually does.

---

# 🔥 BurnoutRadar
> **Explanation**: This is the main title of the project, establishing the name of the app.

BurnoutRadar is a real-time burnout detection system using behavioural biometrics. It monitors mouse movements, typing dynamics, and session patterns to estimate cognitive fatigue without accessing actual keystroke content.
> **Explanation**: This is a brief summary of what the project does. It explains the core concept (detecting burnout via behavioural biometrics) and reassures the reader about privacy (it doesn't log actual keystrokes).

## Setup and Running
> **Explanation**: Marks the start of the section that explains how to get the project working on a local machine.

The project requires running three separate processes: the backend server, the frontend dashboard, and the data simulator (which acts as the user tracking agent for demo purposes).
> **Explanation**: This sentence clarifies the architecture to the user; they need to understand that this isn't just one program, but three different interconnected pieces that must run simultaneously on their computer.

### Prerequisites
> **Explanation**: The section defining software that must be installed on your computer before you can even begin.

Ensure you have the following installed on your machine:
- Node.js (v16+ recommended)
- Python (3.9+ recommended)
> **Explanation**: A list telling the user they must install Node.js (which is required to manage and run the React frontend) and Python (which runs the FastAPI backend and simulator script) beforehand.

---

### Step 1: Start the Backend Server
> **Explanation**: Beginning the instructions specifically for starting the Python backend component.

The backend is built with FastAPI and handles data ingestion, feature extraction, burnout scoring, and WebSocket connections.
> **Explanation**: A brief clarification of the technologies used for the backend (FastAPI) and exactly what its role in the system is (taking data, calculating scores, and sending that data to the frontend in real-time).

**1. Open a terminal and navigate to the `backend` folder:**
   ```bash
   cd burnout-radar/backend
   ```
> **Explanation**: The step telling the user to use the `cd` (change directory) command to enter the `backend` folder where the Python code lives.

**2. Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
> **Explanation**: This command uses Python's package manager (`pip`) to read the `requirements.txt` file and download/install all necessary third-party libraries (like FastAPI, uvicorn, scikit-learn) so the code has what it needs to run.

**3. Run the backend server:**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
> **Explanation**: The actual command to start the web server. It uses the `uvicorn` tool to run the FastAPI `app` defined inside the `main.py` file. The `--reload` flag means it will auto-restart if you edit the code, and `--port 8000` forces it to run on network port 8000.

   *The API will be available at `http://localhost:8000`.*
> **Explanation**: A note letting the user know the local web address where the backend API is now listening for connections.

---

### Step 2: Start the Frontend Dashboard
> **Explanation**: Beginning the instructions for starting the React user interface.

The dashboard is built with React and Vite. It consumes the API and WebSocket feeds to visualize the data.
> **Explanation**: Briefly explains what tech the frontend employs (React and Vite) and its purpose (visualizing the data pulled from the backend so humans can read it).

**1. Open a new terminal window and navigate to the `dashboard` folder:**
   ```bash
   cd burnout-radar/dashboard
   ```
> **Explanation**: Emphasizes opening a *new* terminal window (because the backend is occupying the first one) and navigating into the `dashboard` folder.

**2. Install npm dependencies:**
   ```bash
   npm install
   ```
> **Explanation**: This uses Node Package Manager (`npm`) to look at the `package.json` file and download all the required Javascript libraries (like React and Recharts) needed for the UI.

**3. Start the Vite development server:**
   ```bash
   npm run dev
   ```
> **Explanation**: Triggers a script defined in `package.json` called `dev` which starts Vite. This builds the React app temporarily and serves it locally so you can view it.

   *The dashboard will be available at `http://localhost:5173`.*
> **Explanation**: Indicating the specific local URL where the user can view the user interface in their web browser.

---

### Step 3: Run the Data Simulator
> **Explanation**: Instructions on how to generate fake data for testing.

To see live data flowing into the dashboard, you need to run the agent simulator, which generates synthetic tracking events.
> **Explanation**: Explains *why* this step is needed. Because there isn't a real browser extension tracking you right now, we need a script to pretend to be a user generating typing/mouse data so the dashboard has something to show.

**1. Open a new (third) terminal window and navigate to the `agent` folder:**
   ```bash
   cd burnout-radar/agent
   ```
> **Explanation**: Instructs the user to open a third terminal (because the backend and frontend are running in the first two) and change directory into the `agent` folder.

**2. Run the simulator script in a specific scenario. For a demo that gradually builds up from normal to crisis (burnout), use the `ramp` scenario:**
   ```bash
   python simulate.py --user demo --scenario ramp --duration 300 --interval 3
   ```
> **Explanation**: The command to run the Python simulator script. It passes specific instructions to the script: the simulated user's name is "demo", the specific pattern of data to generate is "ramp" (gradually getting worse), it should run for 300 seconds, and send a data packet every 3 seconds.

#### Simulator Options:
> **Explanation**: Defining the possible arguments you can give the simulator script to change how it works.

- `--scenario`: The type of data to generate.
  - `normal` (15-30 score, stable patterns)
  - `fatigue` (40-55 score, slowing down)
  - `burnout` (65-85 score, erratic behavior)
  - `crisis` (85-100 score, near-zero productivity)
  - `ramp` (Gradually transitions from normal to crisis over the duration)
> **Explanation**: Explains what the `--scenario` argument does and lists the 5 specific keywords it accepts, noting what kind of behaviour each one produces.

- `--duration`: Total simulation time in seconds.
- `--interval`: Seconds between each synthetic payload (default is 3s).
> **Explanation**: Explaining the other two command-line arguments the user can tweak to change how long the simulation runs and how fast it updates.

### Demo Experience
> **Explanation**: Summarizing what the user should expect to see happen.

Once everything is running, open the dashboard in your browser. Leave it open while the simulator pushes data. You will see the score gauge react, trends plot out, alerts trigger as patterns worsen, and recommendations adapt to the simulated behavior.
> **Explanation**: Final reassurance setting expectations that as the simulator runs in the background, the UI in their web browser will automatically update, draw charts, and animate dynamically based on the worsening burnout data.
