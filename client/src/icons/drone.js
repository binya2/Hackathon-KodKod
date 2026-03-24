import L from "leaflet";

export const droneIcon = new L.Icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/1830/1830867.png", // רחפן/מטוס UAV
  iconSize: [40, 40],
  iconAnchor: [20, 20],
  className:"recon"
});

export const dronAttack = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/1830/1830867.png", // רחפן/מטוס UAV
  iconSize: [40, 40],
  iconAnchor: [20, 20],
  className:"attack",
})