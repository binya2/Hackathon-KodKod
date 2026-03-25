# State Aggregator Service

The **State Aggregator** is the central data hub and "Single Source of Truth" for the Tactical Drone Swarm. It fuses high-frequency telemetry and intelligence data into a unified World State.

## Role in C4I Swarm
- **Data Fusion**: Aggregates `DroneTelemetry` and `TargetTelemetry` into a coherent operational picture.
- **State Persistence**: Maintains an in-memory registry of all active and dormant entities.
- **Real-Time Monitoring**: Provides the primary data source for the Command Center UI.

## Kafka Topics
- **Consumes**:
  - `telemetry.raw`: Raw telemetry from all drones in the fleet.
  - `target.raw`: Real-time position and status updates for identified targets.
- **Produces**:
  - None (Serves as a data sink and API provider).

## API Endpoints
### `GET /api/state`
Returns the complete unified World State.
**Example Response**:
```json
{
  "timestamp": "2024-03-24T12:00:00Z",
  "target_data": [{"target_id": "TGT-1", "position": {"lat": 31.7, "lon": 35.2}, "confidence": 0.95}],
  "recon_data": [{"drone_id": "DRN-1", "flight_status": "ACTIVE", "battery": 88.5}],
  "attack_data": [...]
}
```

## Internal Logic Highlights
- **Asynchronous Processing**: Built with `FastAPI` and `aiokafka` for non-blocking data consumption.
- **In-Memory Cache**: Uses high-performance Python dictionaries to ensure sub-millisecond API response times.
