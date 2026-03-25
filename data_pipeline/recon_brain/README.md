# Recon Brain Microservice

The **Recon Brain** manages the intelligence and surveillance lifecycle, coordinating recon drones to track targets and maintain situational awareness.

## Role in C4I Swarm
- **Autonomous Tracking**: Calculates navigation waypoints for recon drones to orbit targets.
- **Intelligence Scrambling**: Automatically manages the deployment of recon assets from the "Warm Pool."
- **Capacity Management**: Ensures optimal coverage by maintaining up to five active recon units per instance.

## Kafka Topics
- **Consumes**:
  - `target.raw`: Used to determine target locations for tracking.
  - `telemetry.raw`: Monitors drone status for deployment decisions.
  - `commands.deployment`: Triggers for new recon missions.
- **Produces**:
  - `commands.drones`: Navigation and status commands for drones.

## Internal Logic Highlights
- **Altitude Offsetting**: Recon drones are commanded to a fixed altitude of 200 m above targets to optimize field of view.
- **Warm Pool Scaling**: Automatically transitions drones from `SLEEP` to `ACTIVE` flight status upon deployment requests.
- **Smart Scaling**: 
  - **Docker Compose**: Uses message re-production to Kafka with unique keys for horizontal distribution.
  - **Kubernetes**: Detects `RUNNING_IN_K8S` and relies on the **Horizontal Pod Autoscaler (HPA)** for scaling, preventing message loops.
