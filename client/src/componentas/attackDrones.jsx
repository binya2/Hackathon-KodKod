import SmoothMarker from "./smoothMarker";

export default function AttackDrones({ squads }) {
  if (!squads) return null;

  return squads.map((squad) =>
    squad.drones.map((drone) => (
      <SmoothMarker
        key={drone.drone_id}
        position={[drone.telemetry.lat, drone.telemetry.lon]}
      />
    ))
  )
}