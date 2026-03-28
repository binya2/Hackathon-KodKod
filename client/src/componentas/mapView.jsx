import { MapContainer, TileLayer, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import ReconDrone from "./reconDrone";
import AttackDrones from "./attackDrones";
import Target from "./target";
import { MapController } from "./mapController";
import ExplosionMarker from "./explosionMarker";

export default function MapView({ data, manualDrone, setManualDrone, explosionPos, droneTrails }) {
  // 1. קביעת מרכז המפה בצורה בטוחה
  const center = (data && data.recon_data && data.recon_data.length > 0) 
    ? [data.recon_data[0].position.lat, data.recon_data[0].position.lon]
    : [31.7, 35.2];

  // 2. ה-return חייב להיות מחוץ לכל תנאי if כדי שהמפה תמיד תרונדר
  return (
    <MapContainer 
      center={center} 
      zoom={13} 
      style={{ height: "100vh", width: "100%" }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      
      {/* 3. הצגת פיצוץ */}
      {explosionPos && <ExplosionMarker position={explosionPos} />}
      
      {/* 4. רינדור רכיבי המערכת */}
      {data && (
        <>
          <ReconDrone data={data.recon_data} setManualDrone={setManualDrone} />
          <AttackDrones data={data.attack_data} />
          <Target data={data.target_data} />
        </>
      )}

      {/* 5. בקר שליטה ידנית */}
      <MapController 
        manualDrone={manualDrone}
        onMove={(lat, lon) => {
          if (!manualDrone) return; // הגנה למקרה שאין רחפן נבחר
          fetch("http://localhost:3001/api/actions/navigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              drone_id: manualDrone.drone_id,
              lat: lat,
              lon: lon // תיקון טעות כתיב שהייתה לך (lon, lon)
            }),
          }).catch(err => console.error("Navigation failed", err));
        }}
      />

      {/* 6. רינדור השובל (Trails) */}
      {droneTrails && Object.entries(droneTrails).map(([droneId, positions]) => (
        <Polyline
          key={`trail-${droneId}`}
          positions={positions}
          pathOptions={{
            // כחול לתצפית (DRN), אדום לתקיפה
            color:"white",
            weight: 3,
            opacity: 0.6,
            dashArray: '10, 20' // קו מקווקו למראה טקטי
          }}
        />
      ))}
    </MapContainer>
  );
}