# ezAIoT Home Assistant Integration

ezAIoT is a Home Assistant custom integration distributed through HACS.
This initial package provides the integration entry and a single-instance
configuration flow. Device discovery and the application panel are developed
as separate features.

This test release can manually download and install the one exact ZHA Quirk
package for Rti-Tek eTRV-ZB01 from the fixed GitHub Release source. It does
not modify YAML, communicate with devices, deploy Zigbee2MQTT converters, or
automatically restart Home Assistant.

The diagnostic sensor reports the number of exact-match ZHA devices. Use
Home Assistant's native **Download diagnostics** action on the integration
page to create a redacted support report.

The `ezAIoT` sidebar panel displays local compatibility status and a manual
test Release workflow. An administrator can check, install, and roll back one
ezAIoT-managed Release. Installing and rolling back require confirmation.

## Install from Marketplace

1. In Home Assistant, open **Settings > Marketplace**.
2. Open the menu, choose **Custom repositories**, and add
   `https://github.com/QuAnnan2019/ezAIoT-HACS` as an **Integration**.
3. Find **ezAIoT**, install it, and restart Home Assistant when prompted.
4. Open **Settings > Devices & services > Add integration**, then add
   **ezAIoT**.
5. Open **ezAIoT** from the sidebar to view local compatibility status.

## Test Release Scope

This test mode reads local device and entity registries for exact-match
Rti-Tek eTRV-ZB01 devices and can contact the fixed GitHub Release source
only when the update coordinator or an administrator requests a check.

The Release ZIP is installed only below `/config/zha_quirks/ezaiot/`; existing
files below `/config/zha_quirks/` are left untouched. The previous
ezAIoT-managed version is retained for one explicit rollback. After deploying
or rolling back, configure ZHA's `custom_quirks_path` yourself if needed,
restart Home Assistant, then reconfigure or re-pair the device as appropriate.

The panel labels this feature **Unsigned test mode**. It intentionally does
not yet verify a Release signature or package hash. Use it only with an
isolated test Home Assistant instance. Before a public release, the signed
manifest and package-validation path must replace this test workflow.

## Manual Development Installation

Copy `custom_components/ezaiot` to
`/config/custom_components/ezaiot`, restart Home Assistant, then add `ezAIoT`
from **Settings > Devices & services > Add integration**.

For development requirements, constraints, decisions, and progress, see the
local-only `docs/` directory. It is intentionally excluded from Git.
