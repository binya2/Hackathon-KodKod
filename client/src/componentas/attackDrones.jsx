import SmoothMarker from "./smoothMarker";
import { dronAttack } from "../icons/drone";

export default function AttackDrones({ squads }) {
  if (!squads) return null;

  return squads.map((drone) =>{ 

    return(
      <SmoothMarker
        key={drone.drone_id}
        position={[drone.telemetry.lat, drone.telemetry.lon]}
        icon={dronAttack}
      />
    )})
}