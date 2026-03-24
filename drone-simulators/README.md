# Drone Simulators Service

This service contains the core simulators for the drone swarm system.

## 🚀 Components

1.  **`drones_sim.py`**: Simulates multiple drones (recon/attack), publishing telemetry to the `telemetry.raw` Kafka topic. It also broadcasts MAVLink packets over UDP.
2.  **`target_sim.py`**: Simulates a moving target, publishing its position to the `target.raw` Kafka topic.

## 📦 Requirements

- Python 3.11+
- Kafka (included in `docker-compose.yml`)

## 🛠️ Usage

### 1. Start Infrastructure
```bash
docker compose up -d
```

### 2. Run Drone Simulation
```bash
python drones_sim.py --num-drones 5
```

### 3. Run Target Simulation
```bash
python target_sim.py
```

## 🐋 Docker

You can build and run this service as a container:
```bash
docker build -t drone-simulators .
docker run --env KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 drone-simulators
```
