# ezAIoT Home Assistant Integration

ezAIoT is a Home Assistant custom integration distributed through HACS.
This initial package provides the integration entry and a single-instance
configuration flow. Device discovery and the application panel are developed
as separate features.

This release does not install Quirks, modify YAML, communicate with devices,
deploy Zigbee2MQTT converters, or send data outside Home Assistant.

The diagnostic sensor reports the number of exact-match ZHA devices. Use
Home Assistant's native **Download diagnostics** action on the integration
page to create a redacted support report.

The `ezAIoT` sidebar panel displays local compatibility status and the Quirk
update-source state. Until a trusted GitHub Release catalog is configured,
the panel makes no GitHub requests and does not deploy Quirks.

## Install from Marketplace

1. In Home Assistant, open **Settings > Marketplace**.
2. Open the menu, choose **Custom repositories**, and add
   `https://github.com/QuAnnan2019/ezAIoT-HACS` as an **Integration**.
3. Find **ezAIoT**, install it, and restart Home Assistant when prompted.
4. Open **Settings > Devices & services > Add integration**, then add
   **ezAIoT**.
5. Open **ezAIoT** from the sidebar to view local compatibility status.

## Demo Scope

This Demo reads Home Assistant's local device and entity registries for
exact-match Rti-Tek eTRV-ZB01 devices. It does not contact GitHub, control
devices, modify ZHA or Zigbee2MQTT, write Quirk files, or change YAML.

## Manual Development Installation

Copy `custom_components/ezaiot` to
`/config/custom_components/ezaiot`, restart Home Assistant, then add `ezAIoT`
from **Settings > Devices & services > Add integration**.

For development requirements, constraints, decisions, and progress, see the
local-only `docs/` directory. It is intentionally excluded from Git.
