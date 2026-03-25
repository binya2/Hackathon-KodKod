# Edge Simulators

This package simulates the physical environment, including the drone fleet and ground targets.

## Components

### 1. Drone Simulator (`drones_sim.py`)
- **Total Silence (Idle Start)**: All 20 drones start in `SLEEP` mode at `0.0` altitude, emitting minimal heartbeat telemetry until activated.
- **Warm Pool Mechanics**: Supports transition from `SLEEP` to `ACTIVE` flight status via Kafka commands.
- **Physics Simulation**: Simple 3D movement, battery depletion, and weapon state management.

### 2. Target Simulator (`target_sim.py`)
- **Event-Driven Activation**: Remains inactive until a `SPAWN_TARGET` event is received on the `events.intel` topic.
- **Battle Damage Assessment (BDA)**: Listens for `PAYLOAD_DROPPED` events. If a payload falls within 100 m, target health is reduced.
- **Destruction Logic**: Once health reaches 0, the target stops emitting valid telemetry and is marked as destroyed.

## Kafka Topics
- **Consumes**: `commands.drones`, `commands.attack`, `events.payload_dropped`, `events.intel`.
- **Produces**: `telemetry.raw`, `target.raw`, `events.payload_dropped` (on strike execution).

## Internal Logic Highlights
- **Euclidean Hit Detection**: Calculates the distance between target base coordinates and payload drop points for damage calculation.
- **Warm Pool Efficiency**: Drones in `SLEEP` status consume zero simulated battery and have reduced processing overhead.
