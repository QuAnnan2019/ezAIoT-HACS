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

## Manual Installation

Copy `custom_components/ezaiot` to
`/config/custom_components/ezaiot`, restart Home Assistant, then add `ezAIoT`
from **Settings > Devices & services > Add integration**.

For development requirements, constraints, decisions, and progress, see the
local-only `docs/` directory. It is intentionally excluded from Git.
