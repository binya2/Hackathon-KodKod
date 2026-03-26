from data_pipeline.shared_models import GeoPoint, TargetTelemetry, TargetType


class TargetState:
    def __init__(self):
        self.target_id: str = "TGT-INIT"
        self.base_lat: float = 31.705
        self.base_lon: float = 35.205
        self.health: float = 100.0
        self.is_active: bool = False
        self._death_broadcasted: bool = False

    def spawn(self, target_id: str, lat: float, lon: float):
        self.target_id = target_id
        self.base_lat = lat
        self.base_lon = lon
        self.health = 100.0
        self.is_active = True
        self._death_broadcasted = False

    def take_damage(self, amount: float):
        if self.is_active:
            self.health = max(0.0, self.health - amount)
            if self.health <= 0:
                self.is_active = False

    def create_telemetry(self, current_lat: float, current_lon: float) -> TargetTelemetry:
        return TargetTelemetry(
            target_id=self.target_id,
            target_type=TargetType.VEHICLE.value,
            position=GeoPoint(lat=current_lat, lon=current_lon),
            confidence=0.95 if self.health > 0 else 0.0,
            health=self.health
        )
