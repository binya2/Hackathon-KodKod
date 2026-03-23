import { Marker, Polygon } from "react-leaflet";
import SmoothMarker from "./smoothMarker";
import { droneIconTarget } from "../icons/target";

export default function Target({ data }) {
  if (!data) return null;
  return (
    <>
      <SmoothMarker position={[data.location.lat, data.location.lon]} icon={droneIconTarget}/>

      {data.predicted_polygon && (
        <Polygon positions={data.predicted_polygon} target={droneIconTarget}/>
      )}
    </>
  );
}