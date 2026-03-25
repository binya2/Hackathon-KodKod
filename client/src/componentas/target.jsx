import { Marker, Polygon } from "react-leaflet";
import SmoothMarker from "./smoothMarker";
import { droneIconTarget } from "../icons/target";

export default function Target({ data }) {
  // console.log(data);
  if (!data) return null;
  return (
    <>
    {data.map((target)=>{

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