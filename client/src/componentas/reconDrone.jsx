import SmoothMarker from "./smoothMarker";
import { Circle } from "react-leaflet";
import { droneIcon } from "../icons/drone";

export default function ReconDrone({ data, setManualDrone, manualDrone }) {
  if (!data) return null;
  return (
    <>
      {data.map((drone) => {
        return (
        
            <SmoothMarker key={drone.drone_id} position={[drone.position.lat, drone.position.lon]} icon={droneIcon}
              eventHandlers={{
                click: () => setManualDrone(drone)
              }}
            />
        
        )
      })}

    </>
  );
}