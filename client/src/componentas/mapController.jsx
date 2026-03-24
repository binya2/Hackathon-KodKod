import { useMapEvents } from "react-leaflet";

export function MapController({ manualDrone, onMove }) {
    useMapEvents({
      click(e) {
        if (!manualDrone) return;
  
        const { lat, lng } = e.latlng;
  
        onMove(lat, lng);
      },
    });
  
    return null;
  }