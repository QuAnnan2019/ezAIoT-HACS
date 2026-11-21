"""Contracts for trusted Quirk Release data types."""

from custom_components.ezaiot.release_models import (
    PackageFile,
    ReleaseManifest,
    ReleaseStatus,
)


def test_release_status_is_safe_to_show_to_the_panel() -> None:
    """The panel receives a stable finite release status."""
    assert ReleaseStatus.UPDATE_AVAILABLE.value == "update_available"
    assert ReleaseStatus.VERIFICATION_FAILED.value == "verification_failed"


def test_manifest_keeps_only_release_metadata() -> None:
    """A signed manifest holds package metadata, not local device data."""
    manifest = ReleaseManifest(
        version="0.0.1",
        platform="zha",
        manufacturer="Rti-Tek",
        model="eTRV-ZB01",
        package_name="ezaiot-zha-etrv-zb01-v0.0.1.zip",
        package_size=12,
        package_sha256="a" * 64,
        files=(PackageFile("rti_tek_etrv_zb01.py", "b" * 64, 3),),
        release_notes="Fix thermostat mode.",
        restart_required=True,
    )

    assert manifest.files[0].path == "rti_tek_etrv_zb01.py"
