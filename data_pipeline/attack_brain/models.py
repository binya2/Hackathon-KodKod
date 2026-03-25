from __future__ import annotations

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_models import (
    GeoPoint,
    DroneTelemetry,
    TargetTelemetry,
    DroneCommand
)
