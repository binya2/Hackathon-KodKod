import json
from datetime import datetime
from models import DroneTelemetry, TargetTelemetry, WorldState, DroneRole, GeoPoint, TargetType


# %% Mock Data Generation Cell

def generate_mock_json(output_path: str = "mock_data.json"):
    """
    Instantiates Pydantic models with dummy data for UI/Fullstack testing.
    Exports to a JSON file.
    """

    # 1. Create Mock Drones
    drones = [
        DroneTelemetry(
            drone_id="DRONE_RECON_01",
            role=DroneRole.RECON,
            position=GeoPoint(lat=32.0853, lon=34.7818, alt=150.0),
            velocity=15.5,
            heading=90.0,
            battery_percent=88.5
        ),
        DroneTelemetry(
            drone_id="DRONE_ATTACK_01",
            role=DroneRole.ATTACK,
            position=GeoPoint(lat=32.0850, lon=34.7810, alt=100.0),
            velocity=25.0,
            heading=45.0,
            battery_percent=92.0
        )
    ]

    # 2. Create Mock Target
    targets = [
        TargetTelemetry(
            target_id="TGT_001",
            target_type=TargetType.VEHICLE,
            position=GeoPoint(lat=32.0860, lon=34.7820),
            estimated_velocity=5.0,
            confidence=0.95
        )
    ]

    # 3. Aggregate into WorldState
    world_state = WorldState(
        timestamp=datetime.now(),
        target_data=targets,
        recon_data=[d for d in drones if d.role == DroneRole.RECON],
        attack_data=[d for d in drones if d.role == DroneRole.ATTACK],
        predictions=[]
    )

    # 4. Export to JSON
    with open(output_path, "w") as f:
        # Use Pydantic's model_dump to handle datetime/enum serialization
        json.dump(world_state.model_dump(mode='json'), f, indent=4)

    print(f"Successfully exported mock data to {output_path}")


# %% Execution

if __name__ == "__main__":
    generate_mock_json()
