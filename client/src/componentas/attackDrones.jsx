import SmoothMarker from "./smoothMarker";
import { dronAttack } from "../icons/drone";

export default function AttackDrones({ data }) {
  if (!data) return null;

  return data.map((drone) =>{ 

    return(
      <SmoothMarker
        key={drone.drone_id}
        position={[drone.position.lat, drone.position.lon]}
        icon={dronAttack}
      />
    )})
}