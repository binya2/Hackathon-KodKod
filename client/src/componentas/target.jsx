import { Marker, Polygon } from "react-leaflet";
import SmoothMarker from "./smoothMarker";

export default function Target({ data }) {
  if (!data) return null;

  return (
    <>
      <SmoothMarker position={[data.location.lat, data.location.lon]} />

      {data.predicted_polygon && (
        <Polygon positions={data.predicted_polygon} />
      )}
    </>
  );
}