import { useEffect, useState } from "react";
import MapView from "./componentas/mapView";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import AttackPanel from "./componentas/attackPanel";
import VideoPanel from "./componentas/videoPanel";

// const WS_URL = "ws://localhost:8000/ws";

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function App() {
  const [data, setData] = useState(null);
  const handleEngage = (droneId) => {
    fetch("http://localhost:8000/engage", {
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
  };

  // useEffect(() => {
  //   const ws = new WebSocket(WS_URL);

  //   ws.onmessage = (event) => {
  //     const parsed = JSON.parse(event.data);
  //     setData(parsed);
  //   };

  //   ws.onopen = () => console.log("WS Connected");
  //   ws.onclose = () => console.log("WS Disconnected");

  //   return () => ws.close();
  // }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setData({
        target_data: {
          location: { lat: 31.7 + Math.random() * 0.01, lon: 35.2 },
          predicted_polygon: [
            [31.7, 35.2],
            [31.71, 35.21],
            [31.69, 35.22],
          ],
        },
        recon_data: {
          telemetry: { lat: 31.7, lon: 35.2 },
        },
        attack_data: {
          squads: [
            {
              drones: [
                {
                  drone_id: "1",
                  telemetry: { lat: 31.705, lon: 35.205 },
                },
                {
                  drone_id: "1",
                  telemetry: { lat: 32.70, lon: 35.205 },
                },
              ],
            },
          ],
        },
      });
    }, 1500);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="h-screen w-screen" style={{ position: "relative", height: "100vh", width: "100%" }}>
      <MapView data={data} />
      <AttackPanel
        squads={data?.attack_data?.squads}
        onEngage={handleEngage}
      />
      <VideoPanel />
    </div>
  );
}
