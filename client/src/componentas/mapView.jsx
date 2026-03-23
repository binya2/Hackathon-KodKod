import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import ReconDrone from "./reconDrone";
import AttackDrones from "./attackDrones";
import Target from "./target";
import { useEffect, useState } from "react";

export default function MapView({ data }) {
    const [date,setDate] = useState(new Date())
    let center
    if(data){
        center = [data.recon_data.telemetry.lat,data.recon_data.telemetry.lon];
    }
     else{
        center = [31.7, 35.2];
     }
     if (data && center[0] === data.recon_data.telemetry.lat){
        return (
            <MapContainer center={center} zoom={13} style={{height:"100vh",width:"100%"}}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        
              {data && (
                <>
                  <ReconDrone data={data.recon_data} />
                  <AttackDrones squads={data.attack_data?.squads} />
                  <Target data={data.target_data} />
                </>
              )}
            </MapContainer>
          )
     }

  }