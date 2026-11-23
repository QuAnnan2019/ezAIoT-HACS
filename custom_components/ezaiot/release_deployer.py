"""Filesystem deployment for manually selected unsigned test Releases."""

from __future__ import annotations

import shutil
import stat
import uuid
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from .const import (
    RELEASE_BACKUP_DIRECTORY,
    RELEASE_MANAGED_DIRECTORY,
    RELEASE_MAX_FILE_BYTES,
    RELEASE_MAX_FILE_COUNT,
    RELEASE_MAX_PACKAGE_BYTES,
)
from .release_models import DeploymentState

_VERSION_FILE = ".ezaiot-release-version"


class ReleaseDeploymentError(ValueError):
    """Raised when an unsigned test package cannot be deployed safely."""


class UnsignedReleaseDeployer:
    """Deploy only the ezAIoT-owned Quirk directory below HA configuration."""

    def __init__(self, config_dir: Path) -> None:
        """Initialize paths rooted at Home Assistant's configuration directory."""
        self._quirks_root = config_dir / "zha_quirks"
        self._managed_path = self._quirks_root / RELEASE_MANAGED_DIRECTORY
        self._backup_path = self._quirks_root / RELEASE_BACKUP_DIRECTORY

    def deploy(self, version: str, package: bytes) -> DeploymentState:
        """Extract a package into staging and atomically replace managed files."""
        if not 0 < len(package) <= RELEASE_MAX_PACKAGE_BYTES:
            raise ReleaseDeploymentError("Test package is too large")
        self._quirks_root.mkdir(parents=True, exist_ok=True)
        stage_path = self._quirks_root / f".ezaiot-stage-{uuid.uuid4().hex}"
        previous_version = self._read_version(self._managed_path)
        moved_current = False
        try:
            stage_path.mkdir()
            self._extract(package, stage_path)
            (stage_path / _VERSION_FILE).write_text(version, encoding="utf-8")
            if self._backup_path.exists():
                if self._backup_path.is_symlink():
                    raise ReleaseDeploymentError("Managed backup must not be a symbolic link")
                shutil.rmtree(self._backup_path)
            if self._managed_path.exists():
                if self._managed_path.is_symlink():
                    raise ReleaseDeploymentError("Managed directory must not be a symbolic link")
                self._managed_path.replace(self._backup_path)
                moved_current = True
            try:
                stage_path.replace(self._managed_path)
            except OSError as err:
                if moved_current:
                    self._backup_path.replace(self._managed_path)
                raise ReleaseDeploymentError("Unable to activate test Release") from err
            return DeploymentState(
                installed_version=version,
                backup_version=previous_version if moved_current else None,
                deployed_at=None,
                last_error=None,
            )
        finally:
            if stage_path.exists():
                shutil.rmtree(stage_path)

    def rollback(self) -> DeploymentState:
        """Swap the managed and last backup directories."""
        if not self._managed_path.is_dir() or not self._backup_path.is_dir():
            raise ReleaseDeploymentError("No test Release backup is available")
        if self._managed_path.is_symlink() or self._backup_path.is_symlink():
            raise ReleaseDeploymentError("Managed directories must not be symbolic links")
        stage_path = self._quirks_root / f".ezaiot-rollback-{uuid.uuid4().hex}"
        active_version = self._read_version(self._managed_path)
        backup_version = self._read_version(self._backup_path)
        try:
            self._managed_path.replace(stage_path)
            try:
                self._backup_path.replace(self._managed_path)
            except OSError as err:
                stage_path.replace(self._managed_path)
                raise ReleaseDeploymentError("Unable to restore test Release backup") from err
            stage_path.replace(self._backup_path)
            return DeploymentState(
                installed_version=backup_version,
                backup_version=active_version,
                deployed_at=None,
                last_error=None,
            )
        finally:
            if stage_path.exists():
                shutil.rmtree(stage_path)

    def _extract(self, package: bytes, stage_path: Path) -> None:
        """Extract only bounded regular files below the staging directory."""
        try:
            archive = zipfile.ZipFile(BytesIO(package))
        except zipfile.BadZipFile as err:
            raise ReleaseDeploymentError("Invalid test package archive") from err
        with archive:
            members = archive.infolist()
            if not 0 < len(members) <= RELEASE_MAX_FILE_COUNT:
                raise ReleaseDeploymentError("Invalid test package file count")
            seen: set[str] = set()
            total_size = 0
            for info in members:
                path = self._safe_path(info)
                if path in seen:
                    raise ReleaseDeploymentError("Duplicate test package file")
                seen.add(path)
                if info.flag_bits & 0x1:
                    raise ReleaseDeploymentError("Encrypted test package files are not allowed")
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ReleaseDeploymentError("Symbolic links are not allowed")
                if info.is_dir() or not 0 <= info.file_size <= RELEASE_MAX_FILE_BYTES:
                    raise ReleaseDeploymentError("Invalid test package file")
                total_size += info.file_size
                if total_size > RELEASE_MAX_PACKAGE_BYTES:
                    raise ReleaseDeploymentError("Test package contents are too large")
                contents = archive.read(info)
                if len(contents) != info.file_size:
                    raise ReleaseDeploymentError("Invalid test package file")
                destination = stage_path.joinpath(*PurePosixPath(path).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(contents)

    @staticmethod
    def _safe_path(info: zipfile.ZipInfo) -> str:
        path = PurePosixPath(info.filename)
        if (
            not info.filename
            or "\\" in info.filename
            or path.is_absolute()
            or ".." in path.parts
            or path.name in {"", "."}
        ):
            raise ReleaseDeploymentError("Unsafe test package path")
        return path.as_posix()

    @staticmethod
    def _read_version(directory: Path) -> str | None:
        try:
            version = (directory / _VERSION_FILE).read_text(encoding="utf-8")
        except OSError:
            return None
        return version or None
