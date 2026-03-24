export default function AttackPanel({ squads, onEngage }) {
    if (!squads) return null;
  
    return (
      <div style={{ position: "absolute", right: 10, top: 10, background: "white", padding: 10 ,zIndex: 9999}}>
        <h3>Attack Panel</h3>
  
        {squads.map((squad) =>
          squad.drones.map((drone) => (
            <div key={drone.drone_id}>
              <p>id: {drone.drone_id}</p>
              <p>Ammo: {drone.weapons_ready}</p>
              <p>Status: {drone.status}</p>
  
              <button
                onClick={() => onEngage(drone.drone_id)}
                disabled={drone.weapons_ready === 0}
              >
                ENGAGE
              </button>
            </div>
          ))
        )}
      </div>
    );
  }