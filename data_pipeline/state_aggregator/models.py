from __future__ import annotations

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models from shared_models
from shared_models import (
    DroneRole, 
    GeoPoint, 
    DroneTelemetry, 
    TargetType, 
    TargetTelemetry, 
    WorldState
)
