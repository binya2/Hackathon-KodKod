import SmoothMarker from "./smoothMarker";
import { Circle } from "react-leaflet";
import { droneIcon } from "../icons/drone";

export default function ReconDrone({ data, setManualDrone, manualDrone }) {
  if (!data) return null;

  const position = [data.telemetry.lat, data.telemetry.lon];
  return (
    <>
      <SmoothMarker position={position} icon={droneIcon}
        eventHandlers={{
          click: () => setManualDrone(data)
        }}
      />
    </> 
  );
}