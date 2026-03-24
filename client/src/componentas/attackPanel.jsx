import { useState } from "react";

export default function AttackPanel({ squads, onEngage }) {
    const [selectedDrone, setSelectedDrone] = useState(null);
    if (!squads) return null;

    return (
        <div style={{ position: "absolute", right: "60px", top: "40px", background: "white", padding: 10, zIndex: 9999, width: "180px", maxWidth: "90vw", boxSizing: "border-box" }}>
            <h3>Attack Panel</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                {squads.map((squad) =>
                    squad.drones.map((drone) => (
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "5px" }} key={drone.drone_id}>
                            <p style={{
                                fontSize: "0.7rem",
                                margin: 0
                            }}>id: {drone.drone_id}</p>
                            {/* <p>Ammo: {drone.weapons_ready}</p>
              <p>Status: {drone.status}</p> */}

                            <button style={{ width: "3rem", fontSize: "0.5rem", height: "1rem", background: "blue", border: 0, color: "white" }}
                                onClick={() => {
                                    setSelectedDrone(drone)
                                }}
                                disabled={drone.weapons_ready === 0}
                            >
                                ENTER
                            </button>
                        </div>

                    ))
                )}
            </div>
            {selectedDrone && (
                <div
                    style={{
                        position: "absolute",
                        top: "120px",
                        right: "10px",
                        background: "blue",
                        color: "white",
                        padding: "10px",
                        borderRadius: "8px",
                        zIndex: 10000,
                        width: "150px"
                    }}
                >
                    <h4>Drone Info</h4>
                    <p>Ammo: {selectedDrone.weapons_ready}</p>
                    <p>Status: {selectedDrone.status}</p>
                    <button
                        style={{
                            width: "100%",
                            background: "red",
                            color: "white",
                            border: "none",
                            padding: "5px",
                            marginTop: "5px"
                        }}
                        onClick={() => {
                            onEngage(selectedDrone.drone_id);
                            setSelectedDrone(null);
                        }}
                    >
                        ENGAGE
                    </button>
                    <button
                        style={{
                            width: "100%",
                            marginTop: "5px"
                        }}
                        onClick={() => setSelectedDrone(null)}
                    >
                        CLOSE
                    </button>
                </div>
            )}
        </div>

    )
}