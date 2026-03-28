import React, { useState } from 'react';

export default function UnifiedDronePanel({ data, onTakeoff, onEngage, onStartMission, onRecall, onManualDeploy, onTarget }) {
    if (!data) return <div className="side-panel">ממתין לנתונים...</div>;
    const [count, setCount] = useState(20)
    const reconDrones = data.recon_data || [];
    const attackDrones = data.attack_data || [];

    return (
        <div className="side-panel" style={{
            position: 'absolute', right: '20px', top: '20px', width: '280px',
            backgroundColor: 'rgba(30, 30, 30, 0.9)', color: 'white',
            padding: '15px', borderRadius: '12px', zIndex: 1000,
            maxHeight: '85vh', overflowY: 'auto', direction: 'rtl',
            boxShadow: '0 4px 15px rgba(0,0,0,0.5)', border: '1px solid #444',
            fontFamily: 'sans-serif'
        }}>
            <h2 style={{ fontSize: '18px', textAlign: 'center', borderBottom: '1px solid #555', paddingBottom: '10px', marginTop: 0 }}>
                🎮 מרכז שליטה ובקרה
            </h2>

            <section style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#222', borderRadius: '8px' }}>
                <h3 style={{ color: '#ffcc00', fontSize: '14px', marginTop: 0 }}>🏁 משימה חדשה</h3>
                <button
                    onClick={() => {
                        const kmInDegrees = 0.009;
                        const randomLat = 31.8 + (Math.random() * 2 - 1) * kmInDegrees;
                        const randomLon = 35.105 + (Math.random() * 2 - 1) * kmInDegrees;
                        onStartMission(randomLat, randomLon)
                    }} // נ"צ ברירת מחדל מהאיפיון
                    style={btnStyle('#ffcc00', false)}
                >
                    צור מטרה והזנק סיור 🛰️
                </button>
            </section>
            <section style={{ marginBottom: '20px' }}>
                <h3 style={{ color: '#00d4ff', fontSize: '16px', marginBottom: '10px' }}>📡 רחפני תצפית ({reconDrones.length})</h3>
                {reconDrones.map((drone) => (
                    <div key={drone.drone_id} style={droneCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>🆔 {drone.drone_id}</span>
                            <span style={{ fontSize: '12px', opacity: 0.8 }}>🔋 {drone.battery_percent}% {drone.battery_percent < 20 && " (סוללה חלשה!)"}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '5px', marginTop: '8px' }}>
                            <button
                                onClick={() => onManualDeploy(drone.role)} // משתמש ב-role הקיים של הרחפן (attack/recon)
                                style={btnStyle('#4CAF50')}
                            >
                                הזנק למטרה 🚀
                            </button>
                            <button
                                onClick={() => onRecall(drone.drone_id)}
                                style={btnStyle('#ff9800')} // צבע כתום לפי המלצות הסטטוס באפיון
                            >
                                חזור לבסיס 🏠
                            </button>
                        </div>
                    </div>
                ))}
                {reconDrones.length === 0 && <div style={{ fontSize: '12px', opacity: 0.5 }}>אין רחפני תצפית זמינים</div>}
            </section>
            <section>
                <h3 style={{ color: '#ff4d4d', fontSize: '16px', marginBottom: '10px' }}>🚀 רחפני תקיפה ({attackDrones.length})</h3>
                {attackDrones.map((drone) => (
                    <div key={drone.drone_id} style={droneCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>🆔 {drone.drone_id}</span>
                            <span style={{ fontSize: '12px' }}>🔋{drone.battery_percent}% {drone.battery_percent < 20 && " (סוללה חלשה!)"}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '5px', marginTop: '8px' }}>

                            <button
                                onClick={() => onManualDeploy(drone.role)} // משתמש ב-role הקיים של הרחפן (attack/recon)
                                style={btnStyle('#4CAF50')}
                            >
                                הזנק למטרה 🚀
                            </button>
                            <button
                                onClick={() => onEngage(drone.drone_id, drone.assigned_target_id)}
                                disabled={drone.weapons_count === 0}
                                style={btnStyle('#f44336', drone.weapons_count === 0)}
                            >
                                תקוף ({drone.weapons_count})
                            </button>
                            <button
                                onClick={() => onRecall(drone.drone_id)}
                                style={btnStyle('#ff9800')} // צבע כתום לפי המלצות הסטטוס באפיון
                            >
                                חזור לבסיס 🏠
                            </button>
                        </div>
                    </div>
                ))}
                {attackDrones.length === 0 && <div style={{ fontSize: '12px', opacity: 0.5 }}>אין רחפני תקיפה זמינים</div>}
            </section>
            {/* רשימת מטרות פעילות בסוף לוח הבקרה */}
            <section style={{ marginTop: '20px', padding: '10px', borderTop: '2px solid #444' }}>
                <h3 style={{ color: '#fff', fontSize: '16px' }}>🎯 מטרות במרחב</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {data?.target_data && data.target_data.length > 0 ? (
                        data.target_data.map((target) => (
                            <div key={target.target_id} style={{
                                padding: '10px',
                                backgroundColor: '#2a2a2a',
                                borderRadius: '5px',
                                borderRight: `4px solid ${target.health > 0 ? '#4caf50' : '#f44336'}`
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: '#eee', fontWeight: 'bold' }}>ID: {target.target_id}</span>
                                    <span style={{ color: target.health < 30 ? 'red' : '#4caf50' }}>
                                        HP: {target.health}%
                                    </span>
                                </div>

                                <div style={{ fontSize: '12px', color: '#aaa', marginTop: '5px' }}>
                                    סטטוס: {target.status || 'Active'} | ביטחון זיהוי: {(target.confidence * 100).toFixed(0)}%
                                </div>

                                <button
                                    onClick={() => onTarget(target.target_id)}
                                    style={{
                                        marginTop: '8px',
                                        width: '100%',
                                        padding: '5px',
                                        backgroundColor: '#d32f2f',
                                        color: 'white',
                                        border: 'none',
                                        cursor: 'pointer',
                                        borderRadius: '3px'
                                    }}
                                >
                                    ❌ ביטול משימה והשמדה
                                </button>
                            </div>
                        ))
                    ) : (
                        <div style={{ color: '#888', fontStyle: 'italic' }}>אין מטרות פעילות כרגע</div>
                    )}
                </div>
            </section>
        </div>
    );
}

// עיצובים קבועים
const droneCardStyle = {
    backgroundColor: '#3d3d3d',
    padding: '10px',
    borderRadius: '8px',
    marginBottom: '10px',
    border: '1px solid #555',
    boxShadow: 'inset 0 0 5px rgba(0,0,0,0.2)'
};

const btnStyle = (color, disabled) => ({
    flex: 1,
    padding: '8px 4px',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: color,
    color: 'white',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: '13px',
    fontWeight: 'bold',
    opacity: disabled ? 0.3 : 1,
    transition: 'opacity 0.2s'
});