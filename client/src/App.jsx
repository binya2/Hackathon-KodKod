import { useEffect, useState } from "react";
import MapView from "./componentas/mapView";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import AttackPanel from "./componentas/attackPanel";
import VideoPanel from "./componentas/videoPanel";
import "./App.css"
import ExplosionMarker from "./componentas/explosionMarker";
import UnifiedDronePanel from "./componentas/attackPanel";


delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function App() {
  const [explosionPos, setExplosionPos] = useState(null);
  const [data, setData] = useState(null);
  const [manualDrone, setManualDrone] = useState(null);
  const handleEngage = async (droneId) => {
    const res = await fetch("http://localhost:8000/engage", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action: "engage",
        target_id: "TGT-1",
        drone_id: droneId,
      }),
    });
    if (res.ok) {
      setExplosionPos({
        lat: data.target_data.location.lat,
        lon: data.target_data.location.lon
      });
      setTimeout(() => setExplosionPos(null), 2000);
    }
  };
  const handleResumeAuto = async (droneId) => {
    await fetch("http://localhost:3001/api/actions/auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drone_id: droneId,
      }),
    });
    setManualDrone(null);
  };

  const handleTakeoff = async (droneId, lat,lon) => {
    try {
      const response = await fetch("http://localhost:3001/api/actions/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drone_id: droneId,
          lat:lat,
          lon,lon
        }),
      });
      if (response.ok) console.log(`Drone ${droneId} launched!`);
    } catch (err) {
      console.error("Takeoff failed", err);
    }
  };

  async function fetchData() {
    const res = await fetch("http://localhost:3001/api/actions/state")
    const dataFetch = await res.json()
    setData(dataFetch)
  }

  useEffect(() => {
    const interval = setInterval(() => {
      fetchData()
    }, 500);
    return () => clearInterval(interval)
  }, []);
  return (
    <div className="h-screen w-screen" style={{ position: "relative", height: "100vh", width: "100%" }}>
      {manualDrone && (
        <button
          onClick={() => handleResumeAuto(manualDrone.drone_id)}
          style={{
            position: "absolute",
            top: "20px",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            backgroundColor: "#ff4d4d",
            color: "white",
            padding: "10px 20px",
            borderRadius: "5px",
            border: "none",
            cursor: "pointer",
            fontWeight: "bold"
          }}
        >AUTO
        </button>
      )}
      <MapView
        data={data}
        manualDrone={manualDrone}
        setManualDrone={setManualDrone}
      >
        {explosionPos && <ExplosionMarker position={explosionPos} />}
      </MapView>
      <UnifiedDronePanel
        data={data}
        onTakeoff={handleTakeoff}
        onEngage={handleEngage}
        onManual={(drone) => setManualDrone(drone)}
      />
      {manualDrone && (
        <button className="resume-btn" onClick={() => handleResumeAuto(manualDrone.drone_id)}>
        </button>
      )}
      <VideoPanel />
    </div>
  );
}
