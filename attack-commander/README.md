# Attack Commander Service (Day 2 - Data Person 1)

This service provides a management interface to trigger drone attacks via an API.

## 🚀 Role
The Attack Commander acts as the bridge between the Fullstack/UI and the Drone Swarm. It translates high-level engagement requests into specific Kafka commands.

## 🛠️ Components

1.  **`main.py`**: A FastAPI service that:
    - Exposes a `POST /engage` endpoint.
    - Validates engagement requests.
    - Publishes `EXECUTE_STRIKE` commands to the `commands.attack` Kafka topic.

## 📦 Requirements
- Python 3.11+
- FastAPI & Uvicorn
- Confluent Kafka Python Client

## 🏃 Usage

### 1. Start the Service
```bash
python main.py
```
The API will be available at `http://localhost:8000`.

### 2. Trigger an Attack
Send a POST request to the `/engage` endpoint:

```bash
curl -X POST http://localhost:8000/engage \
     -H "Content-Type: application/json" \
     -d '{
           "action": "engage",
           "target_id": "TGT-1",
           "drone_id": "DRN-1"
         }'
```

## 📡 Kafka Output
Messages sent to `commands.attack` look like:
```json
{
  "drone_id": "DRN-1",
  "action": "EXECUTE_STRIKE",
  "target_id": "TGT-1",
  "timestamp": "2026-03-24T..."
}
```

## 🐋 Docker
```bash
docker build -t attack-commander .
docker run -p 8000:8000 --env KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 attack-commander
```
