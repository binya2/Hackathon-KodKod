import { MapContainer, TileLayer, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import ReconDrone from "./reconDrone";
import AttackDrones from "./attackDrones";
import Target from "./target";
import { useState } from "react";
import { MapController } from "./mapController";
import ExplosionMarker from "./explosionMarker";

export default function MapView({ data, manualDrone, setManualDrone, explosionPos, droneTrails }) {
  let center
  if (data) {
    center = [data.recon_data[0].position
      .lat, data.recon_data[0].position.lon];
  }
  else {
    center = [31.7, 35.2];
  }
  if (data && center[0] === data.recon_data[0].position.lat) {
    return (
      <MapContainer center={center} zoom={13} style={{ height: "100vh", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {explosionPos && <ExplosionMarker position={explosionPos} />}
        {data && (
          <>
            <ReconDrone data={data.recon_data} setManualDrone={setManualDrone} />
            <AttackDrones data={data.attack_data} />
            <Target data={data.target_data} />
          </>
        )}
        <MapController manualDrone={manualDrone}
          onMove={(lat, lon) => {
            try {
              fetch("http://localhost:3001/api/actions/navigate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  drone_id: manualDrone.drone_id,
                  lat: lat,
                  lon, lon
                }),
              });
            } catch (err) {
              console.error("Takeoff failed", err);
            }
          }}
        />
        {droneTrails && Object.entries(droneTrails).map(([droneId, positions]) => (
          <Polyline
            key={`trail-${droneId}`}
            positions={positions}
            pathOptions={{
              color: 'black',
              weight: 2,
              opacity: 0.6,
              dashArray: '5, 10',
              smoothFactor: 2 // עוזר במניעת קפיצות ויזואליות בשינויי קואורדינטות
            }}
          />
        ))}
      </MapContainer>
    )
  }

}