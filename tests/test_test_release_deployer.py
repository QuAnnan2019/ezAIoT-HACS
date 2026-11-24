"""Filesystem contracts for the temporary ezAIoT Quirk deployer."""

import io
import zipfile
from pathlib import Path

import pytest

from custom_components.ezaiot.release_deployer import (
    ReleaseDeploymentError,
    UnsignedReleaseDeployer,
)


def _package(entries: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, contents in entries:
            archive.writestr(path, contents)
    return buffer.getvalue()


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
    assert (quirks_root / "rti_tek_etrv_zb01.py").read_bytes() == b"second"
    assert (
        quirks_root / ".ezaiot-backup" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"first"


def test_deployer_rolls_back_and_retains_the_replaced_version(tmp_path: Path) -> None:
    deployer = UnsignedReleaseDeployer(tmp_path)
    deployer.deploy("0.0.1", _package([("rti_tek_etrv_zb01.py", b"first")]))
    deployer.deploy("0.0.2", _package([("rti_tek_etrv_zb01.py", b"second")]))

    state = deployer.rollback()

    quirks_root = tmp_path / "zha_quirks"
    assert state.installed_version == "0.0.1"
    assert state.backup_version == "0.0.2"
    assert (quirks_root / "rti_tek_etrv_zb01.py").read_bytes() == b"first"
    assert (
        quirks_root / ".ezaiot-backup" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"second"


def test_deployer_migrates_legacy_managed_directory_to_quirk_root(
    tmp_path: Path,
) -> None:
    quirks_root = tmp_path / "zha_quirks"
    legacy_path = quirks_root / "ezaiot"
    legacy_path.mkdir(parents=True)
    (legacy_path / "rti_tek_etrv_zb01.py").write_bytes(b"legacy")
    (legacy_path / ".ezaiot-release-version").write_text("0.0.1", encoding="utf-8")

    state = UnsignedReleaseDeployer(tmp_path).deploy(
        "0.0.2",
        _package([("rti_tek_etrv_zb01.py", b"fixed")]),
    )

    assert state.installed_version == "0.0.2"
    assert state.backup_version is None
    assert (quirks_root / "rti_tek_etrv_zb01.py").read_bytes() == b"fixed"
    assert not legacy_path.exists()


def test_deployer_does_not_overwrite_unmanaged_root_file(tmp_path: Path) -> None:
    quirks_root = tmp_path / "zha_quirks"
    quirks_root.mkdir()
    target = quirks_root / "rti_tek_etrv_zb01.py"
    target.write_bytes(b"user")

    with pytest.raises(ReleaseDeploymentError, match="managed"):
        UnsignedReleaseDeployer(tmp_path).deploy(
            "0.0.1",
            _package([("rti_tek_etrv_zb01.py", b"release")]),
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
        tmp_path / "zha_quirks" / "rti_tek_etrv_zb01.py"
    ).read_bytes() == b"first"
