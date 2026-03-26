import { Marker, Polygon, Popup } from "react-leaflet";
import SmoothMarker from "./smoothMarker";
import { droneIconTarget } from "../icons/target";

export default function Target({ data }) {
  if (!data) return null;
  return (
    <>
    {data.filter(t=>t.health > 0)
    .map((target)=>{
      return(
      <div key={target.target_id}>
        <SmoothMarker position={[target.position.lat, target.position.lon]} icon={droneIconTarget}/>
        {target.predicted_polygon && (
          <Polygon positions={target.predicted_polygon} target={droneIconTarget}/>
        )}
        </div>
      )

    })}
    </>
  );
}