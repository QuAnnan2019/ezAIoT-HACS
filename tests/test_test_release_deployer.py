"""Filesystem contracts for the temporary ezAIoT Quirk deployer."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from custom_components.ezaiot.managed_quirks import CATALOG_FILE_NAME
from custom_components.ezaiot.release_deployer import (
    ReleaseDeploymentError,
    UnsignedReleaseDeployer,
)


def _package(entries: list[tuple[str, bytes]]) -> bytes:
    quirks = [
        {
            "file": path,
            "manufacturer": "Rti-Tek",
            "model": "eTRV-ZB01" if path == "rti_tek_etrv_zb01.py" else "STHZB",
        }
        for path, _ in entries
        if path.endswith(".py") and "/" not in path and "\\" not in path
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, contents in entries:
            archive.writestr(path, contents)
        archive.writestr(
            CATALOG_FILE_NAME,
            json.dumps({"schema_version": 1, "quirks": quirks}),
        )
    return buffer.getvalue()


def test_ensure_managed_directory_creates_only_the_missing_path(tmp_path: Path) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)

    deployer.ensure_managed_directory()

    managed_directory = tmp_path / "zha_quirks" / "ezaiot"
    assert managed_directory.is_dir()
    assert list(managed_directory.iterdir()) == []


def test_ensure_managed_directory_preserves_existing_directory_contents(
    tmp_path: Path,
) -> None:
    managed_directory = tmp_path / "zha_quirks" / "ezaiot"
    managed_directory.mkdir(parents=True)
    user_file = managed_directory / "user_quirk.py"
    user_file.write_text("user", encoding="utf-8")
    deployer = UnsignedReleaseDeployer(tmp_path)

    deployer.ensure_managed_directory()

    assert user_file.read_text(encoding="utf-8") == "user"


def test_deployer_installs_to_configured_quirk_root_and_keeps_user_files(
    tmp_path: Path,
) -> None:
    quirks_root = tmp_path / "zha_quirks"
    user_quirk = quirks_root / "user_quirk.py"
    user_quirk.parent.mkdir(parents=True)
    user_quirk.write_text("user", encoding="utf-8")
    deployer = UnsignedReleaseDeployer(tmp_path)

    first = deployer.deploy("0.0.1", _package([("rti_tek_etrv_zb01.py", b"first")]))
    second = deployer.deploy("0.0.2", _package([("rti_tek_etrv_zb01.py", b"second")]))

    assert first.installed_version == "0.0.1"
    assert second.installed_version == "0.0.2"
    assert second.backup_version == "0.0.1"
    assert user_quirk.read_text(encoding="utf-8") == "user"
    assert (quirks_root / "ezaiot" / "rti_tek_etrv_zb01.py").read_bytes() == b"second"
    assert (
        quirks_root / "ezaiot" / ".ezaiot-backup" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"first"


def test_deployer_rolls_back_and_retains_the_replaced_version(tmp_path: Path) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)
    deployer.deploy("0.0.1", _package([("rti_tek_etrv_zb01.py", b"first")]))
    deployer.deploy("0.0.2", _package([("rti_tek_etrv_zb01.py", b"second")]))

    state = deployer.rollback()

    quirks_root = tmp_path / "zha_quirks"
    assert state.installed_version == "0.0.1"
    assert state.backup_version == "0.0.2"
    assert (quirks_root / "ezaiot" / "rti_tek_etrv_zb01.py").read_bytes() == b"first"
    assert (
        quirks_root / "ezaiot" / ".ezaiot-backup" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"second"


def test_deployer_rolls_back_a_two_quirk_release_without_leaving_new_files(
    tmp_path: Path,
) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)
    deployer.deploy("0.0.2", _package([("rti_tek_etrv_zb01.py", b"old")]))
    deployer.deploy(
        "0.0.3",
        _package(
            [
                ("rti_tek_etrv_zb01.py", b"new-etrv"),
                ("rti_tek_sthzb.py", b"new-sthzb"),
            ]
        ),
    )

    state = deployer.rollback()

    quirks_root = tmp_path / "zha_quirks"
    assert state.installed_version == "0.0.2"
    assert (quirks_root / "ezaiot" / "rti_tek_etrv_zb01.py").read_bytes() == b"old"
    assert not (quirks_root / "ezaiot" / "rti_tek_sthzb.py").exists()
    assert (
        quirks_root / "ezaiot" / ".ezaiot-backup" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"new-etrv"
    assert (
        quirks_root / "ezaiot" / ".ezaiot-backup" / "rti_tek_sthzb.py"
    ).read_bytes() == b"new-sthzb"


def test_deployer_replaces_owned_package_in_managed_directory(
    tmp_path: Path,
) -> None:
    quirks_root = tmp_path / "zha_quirks"
    deployer = UnsignedReleaseDeployer(tmp_path)
    deployer.deploy("0.0.1", _package([("rti_tek_etrv_zb01.py", b"old")]))
    state = deployer.deploy("0.0.2", _package([("rti_tek_etrv_zb01.py", b"new")]))
    assert state.backup_version == "0.0.1"
    assert (quirks_root / "ezaiot" / "rti_tek_etrv_zb01.py").read_bytes() == b"new"


def test_deployer_does_not_touch_unmanaged_parent_file(tmp_path: Path) -> None:
    quirks_root = tmp_path / "zha_quirks"
    quirks_root.mkdir()
    target = quirks_root / "rti_tek_etrv_zb01.py"
    target.write_bytes(b"user")

    UnsignedReleaseDeployer(tmp_path).deploy(
        "0.0.1", _package([("rti_tek_etrv_zb01.py", b"release")])
    )

    assert target.read_bytes() == b"user"


@pytest.mark.parametrize("path", ["../outside.py", "/absolute.py"])
def test_deployer_rejects_unsafe_package_paths(tmp_path: Path, path: str) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)

    with pytest.raises(ReleaseDeploymentError, match="(?i)unsafe"):
        deployer.deploy("0.0.1", _package([(path, b"bad")]))


def test_deployer_rejects_symlink_and_preserves_current_version(tmp_path: Path) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)
    deployer.deploy("0.0.1", _package([("rti_tek_etrv_zb01.py", b"first")]))
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        entry = zipfile.ZipInfo("link.py")
        entry.external_attr = 0o120777 << 16
        zip_file.writestr(entry, b"target")

    with pytest.raises(ReleaseDeploymentError, match="(?i)symbolic"):
        deployer.deploy("0.0.2", archive.getvalue())

    assert (
        tmp_path / "zha_quirks" / "ezaiot" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"first"
