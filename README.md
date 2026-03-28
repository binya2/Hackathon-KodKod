# 🚁 Autonomous Drone Swarm C2 System

A state-of-the-art, Event-Driven Command and Control (C2) system for managing an autonomous swarm of recon and attack drones. 

This project demonstrates a highly scalable, distributed microservices architecture designed to handle real-time telemetry, dynamic resource allocation, human-in-the-loop (HITL) overrides, and complex physical edge-case simulations.

## 🌟 System Overview
The platform simulates a live battlefield where a commander can designate targets on a map. Behind the scenes, "Autonomous Brains" orchestrate the deployment, navigation, and attack sequences of multiple drones, fully taking into account real-world constraints such as physical distance, battery life, ammunition limits, and strict "Recon-First" protocols.

## 🏗️ Architecture & Tech Stack

The system is fully containerized and divided into specialized microservices talking over an event bus:

* **Frontend (UI/UX):** React.js + Leaflet for high-performance 10Hz live map rendering.
* **API Gateway:** Node.js (Express) providing REST endpoints and WebSocket streams.
* **Infrastructure (Data Layer):**
    * **Apache Kafka:** High-throughput event bus (Pub/Sub) for telemetry and commands.
    * **Redis:** In-memory store holding the absolute real-time "World State".
    * **MongoDB:** Persistent archive for storing drone flight history.
* **Python Microservices (The Logic & Edge):**
    * 🧠 `attack_brain` / `recon_brain`: AI controllers managing drone assignments.
    * 🎮 `attack_commander`: The central FastAPI validating and routing human commands.
    * 📊 `state_aggregator`: Consumes Kafka streams and builds the World State in Redis.
    * 🛸 `drone_sim` / `target_sim`: Edge simulators with realistic physics (speed, battery, payloads).
    * 📚 `history_writer`: Dumps completed telemetry into MongoDB for trail rendering.

## 🚀 Key Features

* **Auto-Deployment (Auto-Scramble):** Designating a target automatically wakes up 1 Recon and 2 Attack drones and assigns them intercept vectors.
* **Manual Override & Auto-Resume:** Operators can seize manual control of any drone mid-flight (`MANUAL_MOVE`), overriding the AI. A single click (`RESUME_AUTO`) returns the drone to autonomous execution without amnesia.
* **Dynamic U-Turns (Abort Mission):** Canceling a target mid-flight instantly updates the global state, causing all assigned drones to abort their dive and automatically return to base (RTB).
* **Real-World Constraints:** Drones will automatically RTB if their battery drops below 20% or if they run out of ammo. The swarm dynamically requests replacement drones to ensure mission success.
* **Fault Tolerance:** The system handles disconnected simulators, ghost targets, and double-kill scenarios gracefully without crashing.

## ⚙️ Quick Start (One-Click Deploy)

The entire architecture (Databases, Python Backends, Node Server, and React Client) is orchestrated via Docker Compose.

1. Clone the repository.
2. Run the deployment command from the root directory:
```bash
docker compose up --build -d
```
3. Access the interfaces:
   * **Live Command Map (React):** `http://localhost:5173`
   * **Node.js Gateway:** `http://localhost:3001`
   * **State Aggregator API:** `http://localhost:8000`
   * **Commander API:** `http://localhost:8001`

## 🧪 Comprehensive Testing Suite
The project includes a robust, fully automated 9-stage asynchronous testing suite (`test/run_tests.py`) validating:
1. Security & Data Validation
2. End-to-End Mission Flow
3. Manual Override Retention
4. Edge Cases (Invalid targets, out-of-bounds, dead drones)
5. Recon-First Engagement Rules
6. Multi-Target Stress Testing
7. Mission Abort & Recall logic
8. Extreme Scenarios (Double kills, Idempotency)
9. Ghost Striker Abort (Mid-dive aborts)