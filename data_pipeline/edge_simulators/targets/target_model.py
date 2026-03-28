from data_pipeline.shared.models import GeoPoint, TargetTelemetry, TargetType


class TargetState:
    def __init__(self, target_id: str, lat: float, lon: float):
        self.target_id: str = target_id
        self.base_lat: float = lat
        self.base_lon: float = lon
        self.health: float = 100.0
        self.is_active: bool = True
        self._death_broadcasted: bool = False

    def take_damage(self, amount: float):
        if self.is_active:
            self.health = max(0.0, self.health - amount)
            if self.health <= 0:
                self.is_active = False

    def create_telemetry(self, current_lat: float, current_lon: float) -> TargetTelemetry:
        return TargetTelemetry(target_id=self.target_id, target_type=TargetType.VEHICLE.value,
                               position=GeoPoint(lat=current_lat, lon=current_lon),
                               confidence=0.95 if self.health > 0 else 0.0, health=self.health)
