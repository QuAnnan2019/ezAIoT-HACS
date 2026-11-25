"""Security contracts for signed ezAIoT Quirk Release packages."""

import base64
import hashlib
import io
import json
import zipfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.ezaiot.release_models import PackageFile, ReleaseManifest
from custom_components.ezaiot.release_validator import (
    ReleaseValidationError,
    parse_manifest,
    validate_package,
)


def _public_key_b64(private_key: Ed25519PrivateKey) -> str:
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return base64.b64encode(public_key).decode()


def _manifest_bytes(package: bytes, **overrides: object) -> bytes:
    package_name = "ezaiot-zha-managed-quirks-v0.0.1.zip"
    payload: dict[str, object] = {
        "schema_version": 1,
        "release_version": "0.0.1",
        "platform": "zha",
        "device": {"manufacturer": "Rti-Tek", "model": "eTRV-ZB01"},
        "compatibility": {"home_assistant": ">=2025.1.0", "zha": ">=0"},
        "package": {
            "name": package_name,
            "size": len(package),
            "sha256": hashlib.sha256(package).hexdigest(),
            "files": [],
        },
        "release_notes": "Fix thermostat mode.",
        "restart_required": True,
    }
    payload.update(overrides)
    return json.dumps(payload, separators=(",", ":")).encode()


def _manifest_for_files(files: tuple[PackageFile, ...], package: bytes) -> ReleaseManifest:
    return ReleaseManifest(
        version="0.0.1",
        platform="zha",
        manufacturer="Rti-Tek",
        model="eTRV-ZB01",
        package_name="ezaiot-zha-managed-quirks-v0.0.1.zip",
        package_size=len(package),
        package_sha256=hashlib.sha256(package).hexdigest(),
        files=files,
        release_notes="Fix thermostat mode.",
        restart_required=True,
    )


def _zip_bytes(entries: list[tuple[str, bytes, int | None]]) -> bytes:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        for path, content, external_attr in entries:
            info = zipfile.ZipInfo(path)
            if external_attr is not None:
                info.external_attr = external_attr
            zip_file.writestr(info, content)
    return archive.getvalue()


def test_valid_signature_and_manifest_produce_candidate() -> None:
    private_key = Ed25519PrivateKey.generate()
    package = b"package"
    manifest_bytes = _manifest_bytes(package)
    signature = private_key.sign(manifest_bytes)

    manifest = parse_manifest(manifest_bytes, signature, _public_key_b64(private_key))

    assert manifest.version == "0.0.1"
    assert manifest.manufacturer == "Rti-Tek"


@pytest.mark.parametrize(
    ("overrides", "removed_key"),
    [
        ({"unexpected": True}, None),
        ({}, "restart_required"),
        ({"platform": "zigbee2mqtt"}, None),
        ({"release_version": "release-1"}, None),
    ],
)
def test_manifest_rejects_invalid_contract(
    overrides: dict[str, object],
    removed_key: str | None,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    manifest_data = json.loads(_manifest_bytes(b"package", **overrides))
    if removed_key is not None:
        manifest_data.pop(removed_key)
    manifest_bytes = json.dumps(manifest_data, separators=(",", ":")).encode()

    with pytest.raises(ReleaseValidationError):
        parse_manifest(
            manifest_bytes,
            private_key.sign(manifest_bytes),
            _public_key_b64(private_key),
        )


def test_signature_failure_is_not_a_candidate() -> None:
    private_key = Ed25519PrivateKey.generate()
    manifest_bytes = _manifest_bytes(b"package")

    with pytest.raises(ReleaseValidationError):
        parse_manifest(manifest_bytes, b"x" * 64, _public_key_b64(private_key))


@pytest.mark.parametrize("path", ["/absolute.py", "../parent.py", r"folder\\bad.py"])
def test_zip_rejects_unsafe_paths(path: str) -> None:
    package = _zip_bytes([(path, b"data", None)])
    manifest = _manifest_for_files((), package)

    with pytest.raises(ReleaseValidationError):
        validate_package(package, manifest)


def test_zip_rejects_symlink_duplicate_unknown_and_oversize_entries() -> None:
    package = _zip_bytes(
        [
            ("link.py", b"target", 0o120777 << 16),
            ("duplicate.py", b"first", None),
            ("duplicate.py", b"second", None),
        ]
    )
    manifest = _manifest_for_files((), package)

    with pytest.raises(ReleaseValidationError):
        validate_package(package, manifest)


def test_zip_requires_manifest_file_table_and_hashes() -> None:
    content = b"quirk"
    package = _zip_bytes([("rti_tek_etrv_zb01.py", content, None)])
    manifest = _manifest_for_files(
        (PackageFile("rti_tek_etrv_zb01.py", "0" * 64, len(content)),),
        package,
    )

    with pytest.raises(ReleaseValidationError):
        validate_package(package, manifest)
