import SmoothMarker from "./smoothMarker";
import { Circle } from "react-leaflet";

export default function ReconDrone({ data }) {
  if (!data) return null;

  const position = [data.telemetry.lat, data.telemetry.lon];

  return (
    <>
      <SmoothMarker position={position} />

      <Circle
        center={position}
        radius={300} 
        pathOptions={{
          color: "red",
          fillColor: "red",
          fillOpacity: 0.2,
        }}
      />
    </>
  );
}