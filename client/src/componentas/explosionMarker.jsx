import { Marker } from "react-leaflet";
import L from "leaflet";


export default function ExplosionMarker({ position }) {
  const explosionIcon = L.divIcon({
    className: "explosion-container",
    html: '<div class="blast"></div>',
    iconSize: [100, 100],
    iconAnchor: [50, 50], 
  });

  return <Marker position={[position.lat, position.lon]} icon={explosionIcon} />;
}