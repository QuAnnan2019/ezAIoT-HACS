"""Constants for the ezAIoT integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ezaiot"
INTEGRATION_VERSION: Final = "0.1.1"
DATA_COORDINATOR: Final = "coordinator"
DATA_PANEL_REGISTERED: Final = "ezaiot_panel_registered"
DATA_PANEL_STATIC_REGISTERED: Final = "ezaiot_panel_static_registered"
DATA_WEBSOCKET_REGISTERED: Final = "ezaiot_websocket_registered"
DATA_RELEASE_SERVICE: Final = "release_service"
DATA_RELEASE_COORDINATOR: Final = "release_coordinator"
GUIDANCE_NOTIFICATION_ID: Final = "ezaiot_zha_guidance"
PLATFORMS: Final = ["sensor", "update"]
PANEL_URL_PATH: Final = "ezaiot"
PANEL_MODULE_URL: Final = "/ezaiot-panel/ezaiot-panel.js"
PANEL_COMPONENT_NAME: Final = "ezaiot-panel"
MANUFACTURER_RTI_TEK: Final = "Rti-Tek"
MODEL_ETRV_ZB01: Final = "eTRV-ZB01"
SCAN_INTERVAL: Final = timedelta(minutes=1)
RELEASE_CHECK_INTERVAL: Final = timedelta(hours=6)
RELEASE_API_URL: Final = (
    "https://api.github.com/repos/QuAnnan2019/zigbee-quircks/releases/latest"
)
RELEASE_MANIFEST_NAME: Final = "ezaiot-quirks-manifest-v1.json"
RELEASE_SIGNATURE_NAME: Final = "ezaiot-quirks-manifest-v1.json.sig"
RELEASE_PACKAGE_PREFIX: Final = "ezaiot-zha-managed-quirks-v"
RELEASE_MANAGED_DIRECTORY: Final = "ezaiot"
RELEASE_BACKUP_DIRECTORY: Final = ".ezaiot-backup"
RELEASE_MAX_PACKAGE_BYTES: Final = 2 * 1024 * 1024
RELEASE_MAX_FILE_COUNT: Final = 32
RELEASE_MAX_FILE_BYTES: Final = 512 * 1024
