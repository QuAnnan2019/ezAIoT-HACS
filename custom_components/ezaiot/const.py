"""Constants for the ezAIoT integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ezaiot"
INTEGRATION_VERSION: Final = "0.1.0"
DATA_COORDINATOR: Final = "coordinator"
DATA_PANEL_REGISTERED: Final = "ezaiot_panel_registered"
DATA_PANEL_STATIC_REGISTERED: Final = "ezaiot_panel_static_registered"
DATA_WEBSOCKET_REGISTERED: Final = "ezaiot_websocket_registered"
PLATFORMS: Final = ["sensor"]
PANEL_URL_PATH: Final = "ezaiot"
PANEL_MODULE_URL: Final = "/ezaiot-panel/ezaiot-panel.js"
PANEL_COMPONENT_NAME: Final = "ezaiot-panel"
MANUFACTURER_RTI_TEK: Final = "Rti-Tek"
MODEL_ETRV_ZB01: Final = "eTRV-ZB01"
SCAN_INTERVAL: Final = timedelta(minutes=1)
