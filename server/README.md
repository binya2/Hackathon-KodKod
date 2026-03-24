# Drone Backend (Team/worker FS-1)

This is the tactical server for the Drone Management System. It handles real-time telemetry, autonomous distance calculations (CV Engine), and tactical engagement commands.

##  Features
- **Real-time Telemetry**: Streamed via Socket.io at 2Hz.
- **CV Engine**: Simulates object visibility and distance detection.
- **Tactical API**: Secure endpoints for manual navigation and engagement.
- **ES Modules**: I'm useing Node.js structure (`type: module`).

##  Installation & Setup
1. Enter the server directory:
   ```bash
   cd server