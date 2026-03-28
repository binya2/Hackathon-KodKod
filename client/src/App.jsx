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
  const [droneTrails, setDroneTrails] = useState({});
  const [explosionPos, setExplosionPos] = useState(null);
  const [currentTargetId, setCurrentTargetId] = useState(null);
  const [data, setData] = useState(null);
  const [manualDrone, setManualDrone] = useState(null);
  const handleEngage = async (droneId) => {
    try {
      const res = await fetch("http://localhost:3001/api/actions/engage", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: "engage",
          target_id: currentTargetId,
          drone_id: droneId,
        }),
      });
      const target = data.target_data.find((t) => t.target_id === currentTargetId)
      if (target) {
        setExplosionPos({
          lat: target.position.lat,
          lon: target.position.lon
        });

        setTimeout(() => setExplosionPos(null), 2000);
      }
    } catch (err) {
      console.log(err);
    }
  };
  const handleResumeAuto = async (droneId) => {
    try {
      await fetch("http://localhost:3001/api/actions/auto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drone_id: droneId,
        }),
      });
      setManualDrone(null);
    } catch (err) {
      console.log(err);
    }
  };

  const handleTakeoff = async (droneId, lat, lon) => {
    try {
      const response = await fetch("http://localhost:3001/api/actions/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drone_id: droneId,
          lat: lat,
          lon, lon
        }),
      });
      if (response.ok) console.log(`Drone ${droneId} launched!`);
    } catch (err) {
      console.error("Takeoff failed", err);
    }
  };

  const handleStartMission = async (lat, lon) => {
    try {
      const response = await fetch("http://localhost:3001/api/actions/new_target", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: lat,
          lon: lon
        }),
      });

      if (response.ok) {

        const result = await response.json();
        console.log(result);
        console.log("Mission Started:", result);
        setCurrentTargetId(result.data.target_id);
      }

    } catch (err) {
      console.error("Failed to start mission:", err);
    }
  };

  const handleRecall = async (droneId) => {
    try {
      const response = await fetch("http://localhost:3001/api/actions/recall_drone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drone_id: droneId
        }),
      });

      if (response.ok) {
        console.log(`Recall command sent for drone: ${droneId}`);
        // חיווי אופטימי: עדכון הסטטוס ב-UI לפני הגעת הנתונים מהשרת (מומלץ לפי האפיון)
      }
    } catch (err) {
      console.error("Recall failed:", err);
    }
  };


  const handleManualDeploy = async (role) => {
    if (!currentTargetId) {
      console.error("No active target ID found for deployment");
      return;
    }

    try {
      const response = await fetch("http://localhost:3001/api/actions/deploy_drone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: role, // "attack" או "recon" 
          target_id: currentTargetId // ה-ID שנשמר מה-new_target [cite: 323]
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Deployment request sent:", result);
      }
    } catch (err) {
      console.error("Failed to deploy drone:", err);
    }
  };

  const handleCancelTarget = async (targetId) => {
    try {
      const response = await fetch("http://localhost:3001/api/actions/cancel_target", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_id: targetId
        }),
      });

      if (response.ok) {
        console.log(`Target ${targetId} cancelled successfully`);
        // חיווי אופטימי: אם המטרה הנוכחית בוטלה, נאפס את ה-ID שלה ב-State
        if (currentTargetId === targetId) {
          setCurrentTargetId(null);
        }
      }
    } catch (err) {
      console.error("Failed to cancel target:", err);
    }
  };

  const fetchDroneTrail = async (droneId, targetId) => {
    try {
      const url = `http://localhost:3001/api/actions/drone_history/${droneId}/${targetId}`;
      const response = await fetch(url);
      
      if (response.ok) {
        const historyPoints = await response.json();
        const trailCoordinates = historyPoints.map(p => [p.lat, p.lon]);
  
        setDroneTrails(prev => ({
          ...prev,
          [droneId]: trailCoordinates
        }));
      }
    } catch (err) {
      console.error("Fetch trail error:", err);
    }
  };


  async function fetchData() {
    try {
      const res = await fetch("http://localhost:3001/api/actions/state")
      const dataFetch = await res.json()

      if (dataFetch.target_data && data) {
        dataFetch.target_data.forEach((target) => {
          const oldTarget = data.target_data.find(t => t.target_id === target.target_id);
          if (oldTarget && oldTarget.health > 0 && target.health <= 0) {
            setExplosionPos({
              lat: target.position.lat,
              lon: target.position.lon
            });
            setCurrentTargetId(null)
            setTimeout(() => setExplosionPos(null), 3000)
          }
        })
      }
      const allDrones = [...(dataFetch.recon_data || []), ...(dataFetch.attack_data || [])];
      allDrones.forEach(drone => {
        if (drone.battery_percent < 20 && drone.flight_status !== "RETURNING" && drone.flight_status !== "SLEEP") {
          handleRecall(drone.drone_id);
        }
      });
      setData(dataFetch)
    } catch (err) {
      console.log(err);
    }
  }

  useEffect(() => {
    const interval = setInterval(() => {
      fetchData()
    }, 500);
    return () => clearInterval(interval)
  }, []);
// App.jsx

useEffect(() => {
  // פונקציה פנימית שתרוץ בכל אינטרוול
  const updateTrails = () => {
    if (!data) return;

    // איסוף כל הרחפנים
    const allDrones = [
      ...(data.recon_data || []),
      ...(data.attack_data || [])
    ];

    allDrones.forEach(drone => {
      // בדיקה קריטית: האם יש למטרה ID והאם הוא לא null
      if (drone.assigned_target_id) {
        console.log(`Fetching trail for drone ${drone.drone_id} target ${drone.assigned_target_id}`);
        fetchDroneTrail(drone.drone_id, drone.assigned_target_id);
      }
    });
  };

  // הרצה ראשונה מידית כשיש דאטה
  if (data) {
    updateTrails();
  }

  // הגדרת האינטרוול
  const interval = setInterval(updateTrails, 2000);

  return () => clearInterval(interval);
}, [data]); // חשוב ש-data יהיה כאן כדי שהאינטרוול יתעדכן כשהמידע משתנה
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
        explosionPos={explosionPos}
        droneTrails={droneTrails}
      >
        {explosionPos && <ExplosionMarker position={explosionPos} />}
      </MapView>
      <UnifiedDronePanel
        data={data}
        onTakeoff={handleTakeoff}
        onEngage={handleEngage}
        onManual={(drone) => setManualDrone(drone)}
        onStartMission={handleStartMission}
        onRecall={handleRecall}
        onManualDeploy={handleManualDeploy}
        onTarget={handleCancelTarget}
      />
      {manualDrone && (
        <button className="resume-btn" onClick={() => handleResumeAuto(manualDrone.drone_id)}>
        </button>
      )}
      <VideoPanel />
    </div>
  );
}
