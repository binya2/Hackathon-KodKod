# Attack Brain Microservice

The **Attack Brain** coordinates the kinetic phase of operations, managing attack drone swarms to surround and engage targets effectively.

## Role in C4I Swarm
- **Swarm Coordination**: Synchronizes multiple attack drones around a single target.
- **Airspace De-confliction**: Manages vertical and horizontal separation within the swarm.
- **Autonomous Scrambling**: Deploys attack assets from the idle "Warm Pool" as needed.

## Kafka Topics
- **Consumes**:
  - `target.raw`, `telemetry.raw`, `commands.deployment`.
- **Produces**:
  - `commands.drones`: High-precision navigation commands for strike positioning.

## Internal Logic Highlights
- **Altitude Separation**: To prevent mid-air collisions, each drone in the swarm is assigned a unique flight level (starting at 150m with 20m increments).
- **Dynamic Encirclement**: Calculates offset waypoints around target coordinates for multi-angle engagement.
- **Environment-Aware Scaling**: Integrated with Kubernetes HPA. In K8S mode, the service suppresses internal scaling messages to allow the cluster orchestrator to manage pod replicas based on CPU/Memory load.
