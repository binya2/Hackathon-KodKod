# Attack Commander Service

The **Attack Commander** is the primary Command and Control (C2) interface, providing high-level strategic endpoints for mission execution.

## Role in C4I Swarm
- **Mission Triggering**: The gateway for starting reconnaissance and engagement cycles.
- **Intelligence Injection**: Allows for the manual spawning of targets within the operational area.
- **Strike Authorization**: Issues the final execution commands to attack drones.

## API Endpoints
### `POST /new_target` (Event-Driven Start)
Spawns a target and automatically scrambles a recon drone in a single call.
**Payload**: `{"lat": 31.7, "lon": 35.2}`

### `POST /engage`
Authorizes a specific drone to execute a strike on a target.
**Payload**: `{"action": "engage", "target_id": "TGT-1", "drone_id": "DRN-6"}`

## Kafka Topics
- **Produces**:
  - `events.intel`: Target spawn events (`SPAWN_TARGET`).
  - `commands.deployment`: Requests for new drone deployments.
  - `commands.attack`: Direct strike authorization (`EXECUTE_STRIKE`).

## Internal Logic Highlights
- **The Scramble Trigger**: Implements the "Event-Driven Start" mechanism by simultaneously notifying the target simulator and the recon brain.
- **UUID Load Balancing**: Deployment requests are keyed with random UUIDs to ensure even partition distribution across brain replicas.
