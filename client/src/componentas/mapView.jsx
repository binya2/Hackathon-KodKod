import {MapContainer, TileLayer, Polyline} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import ReconDrone from "./reconDrone";
import AttackDrones from "./attackDrones";
import Target from "./target";
import {MapController} from "./mapController";
import ExplosionMarker from "./explosionMarker";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

export default function MapView({data, manualDrone, setManualDrone, explosionPos, droneTrails}) {
    // Default center for the map
    const defaultCenter = [31.8, 35.1];
    
    // Calculate center based on first recon drone if available
    const center = (data && data.recon_data && data.recon_data.length > 0 && data.recon_data[0].position)
        ? [data.recon_data[0].position.lat, data.recon_data[0].position.lon]
        : defaultCenter;

    return (
        <MapContainer center={center} zoom={13} style={{height: "100vh", width: "100%"}}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
            
            {explosionPos && <ExplosionMarker position={explosionPos}/>}
            
            {data && (
                <>
                    {data.recon_data && <ReconDrone data={data.recon_data} setManualDrone={setManualDrone}/>}
                    {data.attack_data && <AttackDrones data={data.attack_data}/>}
                    {data.target_data && <Target data={data.target_data}/>}
                </>
            )}

            <MapController
                manualDrone={manualDrone}
                onMove={async (lat, lon) => {
                    if (!manualDrone) return;
                    try {
                        await fetch(`${API_BASE_URL}/api/actions/navigate`, {
                            method: "POST",
                            headers: {"Content-Type": "application/json"},
                            body: JSON.stringify({
                                drone_id: manualDrone.drone_id,
                                lat: lat,
                                lon: lon
                            }),
                        });
                    } catch (err) {
                        console.error("Takeoff failed", err);
                    }
                }}
            />

            {droneTrails && Object.entries(droneTrails).map(([droneId, positions]) => (
                positions && positions.length > 0 && (
                    <Polyline
                        key={`trail-${droneId}`}
                        positions={positions}
                        pathOptions={{
                            color: 'black',
                            weight: 2,
                            opacity: 0.6,
                            dashArray: '5, 10',
                            smoothFactor: 2
                        }}
                    />
                )
            ))}
        </MapContainer>
    );
}