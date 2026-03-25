import { useEffect, useState } from "react";
import MapView from "./componentas/mapView";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import AttackPanel from "./componentas/attackPanel";
import VideoPanel from "./componentas/videoPanel";
import "./App.css"
import ExplosionMarker from "./componentas/explosionMarker";

// const WS_URL = "ws://localhost:8000/ws";

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
    await fetch("http://localhost:8000/resume_auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "AUTO",
        drone_id: droneId,
      }),
    });
    setManualDrone(null);
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
        "timestamp": "2026-03-25T08:51:52.870270",
        "target_data": [
          {
            "target_id": "TGT-1",
            "timestamp": "2026-03-25T09:42:33.959680Z",
            "target_type": "vehicle",
            "position": {
              "lat": 31.750026353395903,
              "lon": 35.24992530441729,
              "alt": null
            },
            "confidence": 0.95
          }
        ],
        "recon_data": [
          {
            "drone_id": "DRN-2",
            "timestamp": "2026-03-25T09:42:34.571906Z",
            "role": "recon",
            "position": {
              "lat": 31.1,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 82.48246751214087,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-3",
            "timestamp": "2026-03-25T09:42:34.571990Z",
            "role": "recon",
            "position": {
              "lat": 32.2,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 276.942006294915,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-4",
            "timestamp": "2026-03-25T09:42:34.572054Z",
            "role": "recon",
            "position": {
              "lat": 31.75005000000166,
              "lon": 35.24995000000166,
              "alt": 3.029500000000179
            },
            "velocity": 15.0,
            "heading": 257.38350299948354,
            "battery_percent": 0.0,
            "flight_status": "ACTIVE"
          },
          {
            "drone_id": "DRN-5",
            "timestamp": "2026-03-25T09:42:34.572072Z",
            "role": "recon",
            "position": {
              "lat": 31.3,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 271.34802874022125,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-1",
            "timestamp": "2026-03-25T09:42:34.571650Z",
            "role": "recon",
            "position": {
              "lat": 31.4,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 18.458039112724677,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          }
        ],
        "attack_data": [
          {
            "drone_id": "DRN-9",
            "timestamp": "2026-03-25T09:42:34.572147Z",
            "role": "attack",
            "position": {
              "lat": 31.5,
              "lon": 35.2,
              "alt": 2.600500000000036
            },
            "velocity": 15.0,
            "heading": 234.38384574352386,
            "battery_percent": 0.0,
            "flight_status": "ACTIVE"
          },
          {
            "drone_id": "DRN-14",
            "timestamp": "2026-03-25T09:42:34.572189Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.1,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 133.7950566525932,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-17",
            "timestamp": "2026-03-25T09:42:34.572213Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.3,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 209.39173009872937,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-6",
            "timestamp": "2026-03-25T09:42:34.572084Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.4,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 66.42525173551942,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-10",
            "timestamp": "2026-03-25T09:42:34.572156Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.401,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 152.90308673700875,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-11",
            "timestamp": "2026-03-25T09:42:34.572165Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.402,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 224.86187174562738,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-16",
            "timestamp": "2026-03-25T09:42:34.572205Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.403,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 318.2389661846935,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-20",
            "timestamp": "2026-03-25T09:42:34.572273Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.404,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 129.58657822745303,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-8",
            "timestamp": "2026-03-25T09:42:34.572138Z",
            "role": "attack",
            "position": {
              "lat": 31.7,
              "lon": 35.407,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 56.41450928483234,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-15",
            "timestamp": "2026-03-25T09:42:34.572197Z",
            "role": "attack",
            "position": {
              "lat": 31.120,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 91.4193185608269,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-7",
            "timestamp": "2026-03-25T09:42:34.572128Z",
            "role": "attack",
            "position": {
              "lat": 31.749550000001644,
              "lon": 35.249500000001646,
              "alt": 2.6055000000000375
            },
            "velocity": 15.0,
            "heading": 85.0233202618409,
            "battery_percent": 0.0,
            "flight_status": "ACTIVE"
          },
          {
            "drone_id": "DRN-12",
            "timestamp": "2026-03-25T09:42:34.572172Z",
            "role": "attack",
            "position": {
              "lat": 31.703,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 284.1992841372605,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-13",
            "timestamp": "2026-03-25T09:42:34.572180Z",
            "role": "attack",
            "position": {
              "lat": 31.407,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 157.65648204412688,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-18",
            "timestamp": "2026-03-25T09:42:34.572221Z",
            "role": "attack",
            "position": {
              "lat": 31.408,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 149.070999939052,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          },
          {
            "drone_id": "DRN-19",
            "timestamp": "2026-03-25T09:42:34.572229Z",
            "role": "attack",
            "position": {
              "lat": 31.305,
              "lon": 35.2,
              "alt": 0.0
            },
            "velocity": 15.0,
            "heading": 296.3025416262135,
            "battery_percent": 100.0,
            "flight_status": "SLEEP"
          }
        ]
      });
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
      <AttackPanel
        data={data?.attack_data}
        onEngage={handleEngage}
      />
      <VideoPanel />
    </div>
  );
}
