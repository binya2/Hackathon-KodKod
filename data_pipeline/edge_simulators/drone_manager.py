import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from drone_model import Drone


class DroneManager:
    def __init__(self, num_drones: int, base_lat: float, base_lon: float):
        self.drones = self._initialize_drones(num_drones, base_lat, base_lon)

    def _initialize_drones(self, num: int, lat: float, lon: float) -> List[Drone]:
        drones = []
        for i in range(num):
            role = "recon" if i < 5 else "attack"
            drones.append(Drone(f"DRN-{i + 1}", role, lat, lon, 0.0))
        return drones

    def handle_command(self, cmd_data: Dict[str, Any], topic: str, producer):
        if topic == "commands.deployment":
            self._process_deployment_command(cmd_data)
            return

        drone_id = cmd_data.get("drone_id")
        drone = next((d for d in self.drones if d.drone_id == drone_id), None)

        if not drone:
            return

        if topic == "commands.drones":
            self._process_system_command(drone, cmd_data)
        elif topic == "commands.attack":
            self._process_attack_command(drone, cmd_data, producer)

    def _process_deployment_command(self, cmd: Dict[str, Any]):
        role = cmd.get("role")
        target_id = cmd.get("target_id")
        position = cmd.get("position")

        available_drone = next((d for d in self.drones if d.role == role and d.flight_status == "SLEEP"), None)
        if available_drone and position:
            print(f"🌟 [SIM] Deploying {available_drone.drone_id} ({role}) for target {target_id}")
            available_drone.wake_up(target_id, position.get("lat"), position.get("lon"))
        else:
            if not available_drone:
                print(f"⚠️ [SIM] No available {role} drones for deployment!")
            if not position:
                print(f"⚠️ [SIM] Deployment command for {target_id} is missing position!")

    def _process_system_command(self, drone: Drone, cmd: Dict[str, Any]):
        action = cmd.get("action")
        if action == "WAKE_UP":
            pos = cmd.get("position", {})
            drone.wake_up(cmd.get("target_id"), pos.get("lat"), pos.get("lon"))
        elif action == "RECALL_DRONE":
            drone.recall()
        elif action == "MANUAL_MOVE":
            pos = cmd.get("position", {})
            drone.manual_move(pos.get("lat", drone.lat), pos.get("lon", drone.lon), pos.get("alt", drone.alt))
        elif action == "RESUME_AUTO":
            drone.flight_status = "ACTIVE"
        elif "position" in cmd:
            if drone.flight_status != "ATTACKING":
                pos = cmd.get("position", {})
                drone.update_waypoint(pos.get("lat"), pos.get("lon"), pos.get("alt", drone.alt))
                if "flight_status" in cmd:
                    drone.flight_status = cmd["flight_status"]

    def _process_attack_command(self, drone: Drone, cmd: Dict[str, Any], producer):
        if drone.role.lower() != "attack":
            print(f"⚠️ [SIM] Drone {drone.drone_id} is a {drone.role} drone and cannot perform strikes.")
            return

        if cmd.get("action") == "EXECUTE_STRIKE" and drone.weapons_count > 0:
            target_id = cmd.get("target_id")
            print(f"🎯 [SIM] {drone.drone_id} heading for STRIKE on {target_id}")
            drone.flight_status = "ATTACKING"
            drone.assigned_target_id = target_id
            
            pos = cmd.get("position")
            if pos:
                drone.update_waypoint(pos.get("lat"), pos.get("lon"), drone.alt)

    def _emit_strike_event(self, strike_data: dict, producer):
        event = {
            **strike_data,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        producer.produce("events.payload_dropped", key=strike_data["drone_id"], value=json.dumps(event))

    def update_all(self, dt: float, producer):
        for drone in self.drones:
            strike_event = drone.tick(dt)
            if strike_event:
                self._emit_strike_event(strike_event, producer)
