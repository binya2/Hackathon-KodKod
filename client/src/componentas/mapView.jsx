import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import ReconDrone from "./reconDrone";
import AttackDrones from "./attackDrones";
import Target from "./target";
import { useState } from "react";
import { MapController } from "./mapController";

export default function MapView({ data, manualDrone, setManualDrone }) {
  const [date, setDate] = useState(new Date())
  let center
  if (data) {
    center = [data.recon_data.telemetry.lat, data.recon_data.telemetry.lon];
  }
  else {
    center = [31.7, 35.2];
  }
  if (data && center[0] === data.recon_data.telemetry.lat) {
    return (
      <MapContainer center={center} zoom={13} style={{ height: "100vh", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {data && (
          <>
            <ReconDrone data={data.recon_data} setManualDrone={setManualDrone}/>
            <AttackDrones squads={data.attack_data?.squads} />
            <Target data={data.target_data} />
          </>
        )}
        <MapController manualDrone={manualDrone}
          onMove={(lat, lon) => {
            fetch("http://localhost:8000/move", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                "action": "manual_navigate",
                drone_id: manualDrone.drone_id,
                lat:lat,
                lon:lon,
              }),
            });
          }}
        />
      </MapContainer>
    )
  }

}