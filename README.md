# ezAIoT Home Assistant Integration

ezAIoT is a Home Assistant custom integration distributed through HACS.
This initial package provides the integration entry and a single-instance
configuration flow. Device discovery and the application panel are developed
as separate features.

This test release can manually download and install the exact ZHA Quirk set
declared by a fixed GitHub Release source. It does not modify YAML,
communicate with devices, deploy Zigbee2MQTT converters, or automatically
restart Home Assistant.

The diagnostic sensor reports the number of exact-match ZHA devices declared
by the active managed Release. Use Home Assistant's native **Download
diagnostics** action on the ezAIoT integration page, or the administrator-only
**Download diagnostics** action in the ezAIoT sidebar, to create the same
redacted local support report.

The `ezAIoT` sidebar panel is the primary setup, diagnostics, and support
entry. An administrator explicitly confirms each Release check, installation,
or rollback; none of these actions happen automatically.

## Install from Marketplace

1. In Home Assistant, open **Settings > Marketplace**.
2. Open the menu, choose **Custom repositories**, and add
   `https://github.com/QuAnnan2019/ezAIoT-HACS` as an **Integration**.
3. Find **ezAIoT**, install it, and restart Home Assistant when prompted.
4. Open **Settings > Devices & services > Add integration**, then add
   **ezAIoT**.
5. After restarting Home Assistant, find **ezAIoT** under
   **Settings > Devices & services > Integrations**, or open **ezAIoT** from
   the sidebar to view local compatibility status.

## Test Release Scope

This test mode reads local device and entity registries for exact-match
signatures declared by the active managed Release and can contact the fixed
GitHub Release source only when the update coordinator or an administrator
requests a check.

Before installing a Release, configure ZHA manually:

```yaml
zha:
  custom_quirks_path: /config/zha_quirks/ezaiot/
```

The Release ZIP is installed only in `/config/zha_quirks/ezaiot/`. Its catalog
names every managed Quirk file and exact device signature. Files outside that
directory are never changed. A newer confirmed Release replaces only files
with ezAIoT ownership metadata in the managed directory and retains one
previous managed package in `/config/zha_quirks/ezaiot/.ezaiot-backup/` for
explicit rollback. Restart Home Assistant after deploying or rolling back,
then reconfigure or re-pair the device when the guided setup requests it.

The panel labels this feature **Unsigned test mode**. It intentionally does
not yet verify a Release signature or package hash. Use it only with an
isolated test Home Assistant instance. Before a public release, the signed
manifest and package-validation path must replace this test workflow.

Thread management and Thread network diagnostics are not included in this
ZHA-only integration.

## Manual Development Installation

Copy `custom_components/ezaiot` to
`/config/custom_components/ezaiot`, restart Home Assistant, then add `ezAIoT`
from **Settings > Devices & services > Add integration**.

For development requirements, constraints, decisions, and progress, see the
local-only `docs/` directory. It is intentionally excluded from Git.
