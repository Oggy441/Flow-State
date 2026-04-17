# Running Backend and Dashboard on Separate Laptops

This guide explains how to run the BurnoutRadar backend on one machine and the dashboard on another.

## Quick Start

### Laptop 1: Backend Server

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Run the backend:
   ```bash
   # Windows
   run-backend.bat
   
   # macOS/Linux
   ./run-backend.sh
   ```

3. Find your IP address:
   - **Windows**: Run `ipconfig` in PowerShell, look for "IPv4 Address"
   - **macOS/Linux**: Run `ifconfig` or `ip addr`, look for "inet" address
   - Example: `192.168.1.100`

4. Keep this terminal running. The backend will be accessible at:
   - `http://192.168.1.100:8000` (API)
   - `ws://192.168.1.100:8000` (WebSocket)

### Laptop 2: Dashboard Client

1. Install dependencies:
   ```bash
   cd dashboard
   npm install
   cd ..
   ```

2. Run the dashboard with the backend IP from Laptop 1:
   ```bash
   # Windows
   run-dashboard.bat 192.168.1.100
   
   # macOS/Linux
   ./run-dashboard.sh 192.168.1.100
   ```

3. Open http://localhost:5173 in your browser

4. The dashboard will connect to the backend on Laptop 1

## Manual Configuration (Alternative)

If you prefer to configure manually without the scripts:

### Backend (Laptop 1)

```bash
# Run on all network interfaces
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Dashboard (Laptop 2)

1. Create `.env` in the `dashboard/` folder:
   ```
   VITE_BACKEND_HOST=192.168.1.100
   ```

2. Start the dashboard:
   ```bash
   cd dashboard
   npm run dev
   ```

## Configuration Methods

The dashboard can connect to the backend using one of these methods (in order of priority):

1. **Environment Variable**: `VITE_BACKEND_HOST=<ip-or-hostname>`
   ```bash
   VITE_BACKEND_HOST=192.168.1.100 npm run dev
   ```

2. **`.env` File**: Create `dashboard/.env` with:
   ```
   VITE_BACKEND_HOST=192.168.1.100
   ```

3. **Browser localStorage**: Open browser console and run:
   ```javascript
   localStorage.setItem('backendHost', '192.168.1.100')
   ```

4. **Default**: Uses the same hostname as the dashboard (useful for localhost testing)

## Troubleshooting

### Dashboard can't connect to backend

- **Check network accessibility**: On Laptop 2, run:
  ```bash
  # Windows
  ping 192.168.1.100
  
  # Check if port 8000 is open
  Test-NetConnection 192.168.1.100 -Port 8000
  ```

- **Check firewall**: Make sure port 8000 is allowed in your firewall settings

- **Verify backend is running**: Check Laptop 1 terminal for any error messages

- **Check VITE_BACKEND_HOST**: Ensure it's set correctly in `.env` or environment

### WebSocket connection fails

- Backend must be running with `--host 0.0.0.0`
- Check that all machines are on the same network
- Ensure no firewall is blocking port 8000

## Notes

- The backend now binds to `0.0.0.0` instead of `localhost`, making it accessible from other machines
- CORS is enabled on the backend to allow requests from any origin
- The WebSocket connection is automatically re-attempted if interrupted
- For production deployments, consider using proper SSL/TLS certificates and authentication

## Performance Considerations

- Network latency will be slightly higher than localhost but should be negligible for this application
- Both laptops should be on the same network (WiFi/LAN) for best performance
- The agent script should still run on the backend machine (Laptop 1) to send events
