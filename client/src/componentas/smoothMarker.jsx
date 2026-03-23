import { Marker } from "react-leaflet";
import { useEffect, useRef, useState } from "react";


export default function SmoothMarker({ position,icon }) {
  if(!icon) return null
    const [smoothPos, setSmoothPos] = useState(position);
    const prevPos = useRef(position);
  
    useEffect(() => {
      let frame;
      let start;
      const duration = 400; // ms
  
      const animate = (timestamp) => {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
  
        const lat = prevPos.current[0] + (position[0] - prevPos.current[0]) * progress;
        const lon = prevPos.current[1] + (position[1] - prevPos.current[1]) * progress;
  
        setSmoothPos([lat, lon]);
  
        if (progress < 1) {
          frame = requestAnimationFrame(animate);
        } else {
          prevPos.current = position;
        }
      };
  
      frame = requestAnimationFrame(animate);
  
      return () => cancelAnimationFrame(frame);
    }, [position]);
  
    return <Marker position={smoothPos} icon={icon}/>;
  }