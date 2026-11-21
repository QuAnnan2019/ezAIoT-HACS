"""Validation for signed, bounded ezAIoT Quirk Release packages."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import stat
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .const import (
    MANUFACTURER_RTI_TEK,
    MODEL_ETRV_ZB01,
    RELEASE_MAX_FILE_BYTES,
    RELEASE_MAX_FILE_COUNT,
    RELEASE_MAX_PACKAGE_BYTES,
    RELEASE_PACKAGE_PREFIX,
)
from .release_models import PackageFile, ReleaseManifest

_MANIFEST_KEYS = {
    "schema_version",
    "release_version",
    "platform",
    "device",
    "compatibility",
    "package",
    "release_notes",
    "restart_required",
}
_DEVICE_KEYS = {"manufacturer", "model"}
_PACKAGE_KEYS = {"name", "size", "sha256", "files"}
_FILE_KEYS = {"path", "sha256", "size"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class ReleaseValidationError(ValueError):
    """Raised when a release cannot pass the fixed trust contract."""


def _require_exact_keys(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ReleaseValidationError(f"Invalid {label} fields")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ReleaseValidationError(f"Invalid {label} hash")
    return value


def _require_size(value: object, maximum: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= maximum:
        raise ReleaseValidationError(f"Invalid {label} size")
    return value


def _validate_file_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReleaseValidationError("Invalid package file path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.name in {"", "."}:
        raise ReleaseValidationError("Invalid package file path")
    return path.as_posix()


def _decode_base64(value: str, expected_length: int, label: str) -> bytes:
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, UnicodeEncodeError) as err:
        raise ReleaseValidationError(f"Invalid {label}") from err
    if len(decoded) != expected_length:
        raise ReleaseValidationError(f"Invalid {label}")
    return decoded


def parse_manifest(
    manifest_bytes: bytes,
    signature_bytes: bytes,
    public_key_b64: str,
) -> ReleaseManifest:
    """Verify and parse a manifest without trusting its unverified fields."""
    public_key = _decode_base64(public_key_b64, 32, "public key")
    if len(signature_bytes) != 64:
        raise ReleaseValidationError("Invalid manifest signature")
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            signature_bytes,
            manifest_bytes,
        )
    except InvalidSignature as err:
        raise ReleaseValidationError("Invalid manifest signature") from err

    try:
        raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ReleaseValidationError("Invalid manifest encoding") from err
    manifest = _require_exact_keys(raw_manifest, _MANIFEST_KEYS, "manifest")
    if manifest["schema_version"] != 1:
        raise ReleaseValidationError("Unsupported manifest schema")
    if manifest["platform"] != "zha":
        raise ReleaseValidationError("Unsupported release platform")
    if manifest["restart_required"] is not True:
        raise ReleaseValidationError("Release must require restart")
    version = manifest["release_version"]
    if not isinstance(version, str) or _VERSION_RE.fullmatch(version) is None:
        raise ReleaseValidationError("Invalid release version")
    device = _require_exact_keys(manifest["device"], _DEVICE_KEYS, "device")
    if (
        device["manufacturer"] != MANUFACTURER_RTI_TEK
        or device["model"] != MODEL_ETRV_ZB01
    ):
        raise ReleaseValidationError("Unsupported release device")
    if not isinstance(manifest["compatibility"], dict):
        raise ReleaseValidationError("Invalid compatibility")
    package = _require_exact_keys(manifest["package"], _PACKAGE_KEYS, "package")
    package_name = package["name"]
    expected_name = f"{RELEASE_PACKAGE_PREFIX}{version}.zip"
    if package_name != expected_name:
        raise ReleaseValidationError("Invalid package name")
    package_size = _require_size(
        package["size"],
        RELEASE_MAX_PACKAGE_BYTES,
        "package",
    )
    package_sha256 = _require_sha256(package["sha256"], "package")
    if not isinstance(manifest["release_notes"], str):
        raise ReleaseValidationError("Invalid release notes")
    raw_files = package["files"]
    if not isinstance(raw_files, list) or len(raw_files) > RELEASE_MAX_FILE_COUNT:
        raise ReleaseValidationError("Invalid package files")

    files: list[PackageFile] = []
    paths: set[str] = set()
    for raw_file in raw_files:
        package_file = _require_exact_keys(raw_file, _FILE_KEYS, "package file")
        path = _validate_file_path(package_file["path"])
        if path in paths:
            raise ReleaseValidationError("Duplicate package file")
        paths.add(path)
        files.append(
            PackageFile(
                path=path,
                sha256=_require_sha256(package_file["sha256"], "package file"),
                size=_require_size(
                    package_file["size"],
                    RELEASE_MAX_FILE_BYTES,
                    "package file",
                ),
            )
        )

    return ReleaseManifest(
        version=version,
        platform="zha",
        manufacturer=MANUFACTURER_RTI_TEK,
        model=MODEL_ETRV_ZB01,
        package_name=expected_name,
        package_size=package_size,
        package_sha256=package_sha256,
        files=tuple(files),
        release_notes=manifest["release_notes"],
        restart_required=True,
    )


def validate_package(package_bytes: bytes, manifest: ReleaseManifest) -> dict[str, bytes]:
    """Return only files verified against the signed manifest."""
    if len(package_bytes) != manifest.package_size:
        raise ReleaseValidationError("Package size does not match manifest")
    if hashlib.sha256(package_bytes).hexdigest() != manifest.package_sha256:
        raise ReleaseValidationError("Package hash does not match manifest")

    try:
        archive = zipfile.ZipFile(BytesIO(package_bytes))
    except zipfile.BadZipFile as err:
        raise ReleaseValidationError("Invalid package archive") from err

    expected_files = {package_file.path: package_file for package_file in manifest.files}
    verified_files: dict[str, bytes] = {}
    total_size = 0
    with archive:
        for info in archive.infolist():
            if info.flag_bits & 0x1:
                raise ReleaseValidationError("Encrypted package members are not allowed")
            path = _validate_file_path(info.filename)
            if path in verified_files:
                raise ReleaseValidationError("Duplicate package archive member")
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ReleaseValidationError("Symbolic links are not allowed")
            if info.is_dir() or path not in expected_files:
                raise ReleaseValidationError("Unexpected package archive member")
            if not 0 <= info.file_size <= RELEASE_MAX_FILE_BYTES:
                raise ReleaseValidationError("Package member is too large")
            total_size += info.file_size
            if total_size > RELEASE_MAX_PACKAGE_BYTES:
                raise ReleaseValidationError("Package contents are too large")
            content = archive.read(info)
            expected = expected_files[path]
            if len(content) != expected.size:
                raise ReleaseValidationError("Package member size does not match manifest")
            if hashlib.sha256(content).hexdigest() != expected.sha256:
                raise ReleaseValidationError("Package member hash does not match manifest")
            verified_files[path] = content

    if set(verified_files) != set(expected_files):
        raise ReleaseValidationError("Package contents do not match manifest")
    return verified_files
