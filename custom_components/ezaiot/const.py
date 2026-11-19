"""Constants for the ezAIoT integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ezaiot"
INTEGRATION_VERSION: Final = "0.1.0"
DATA_COORDINATOR: Final = "coordinator"
PLATFORMS: Final = ["sensor"]
MANUFACTURER_RTI_TEK: Final = "Rti-Tek"
MODEL_ETRV_ZB01: Final = "eTRV-ZB01"
SCAN_INTERVAL: Final = timedelta(minutes=1)
