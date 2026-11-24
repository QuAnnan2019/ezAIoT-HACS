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
    """Deploy ezAIoT-managed Quirk files to the configured Quirk root."""

    def __init__(self, config_dir: Path) -> None:
        """Initialize paths rooted at Home Assistant's configuration directory."""
        self._quirks_root = config_dir / "zha_quirks"
        self._legacy_path = self._quirks_root / RELEASE_MANAGED_DIRECTORY
        self._backup_path = self._quirks_root / RELEASE_BACKUP_DIRECTORY

    def deploy(self, version: str, package: bytes) -> DeploymentState:
        """Extract a flat package and activate its files at the Quirk root."""
        if not 0 < len(package) <= RELEASE_MAX_PACKAGE_BYTES:
            raise ReleaseDeploymentError("Test package is too large")
        self._quirks_root.mkdir(parents=True, exist_ok=True)
        stage_path = self._quirks_root / f".ezaiot-stage-{uuid.uuid4().hex}"
        previous_version = self._read_version(self._quirks_root)
        legacy_version = self._read_legacy_version()
        moved_current = False
        try:
            stage_path.mkdir()
            self._extract(package, stage_path)
            package_files = self._package_files(stage_path)
            self._assert_targets_are_managed(package_files, previous_version, legacy_version)
            (stage_path / _VERSION_FILE).write_text(version, encoding="utf-8")

            if previous_version is not None:
                self._replace_backup()
                self._move_active_to_backup(package_files)
                moved_current = True
            elif legacy_version is not None:
                self._remove_backup()

            try:
                self._activate(stage_path, package_files)
            except OSError as err:
                if moved_current:
                    self._restore_backup(package_files)
                raise ReleaseDeploymentError("Unable to activate test Release") from err

            if legacy_version is not None:
                shutil.rmtree(self._legacy_path)

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
        """Restore the last ezAIoT-managed root files from the backup."""
        if not self._backup_path.is_dir() or self._backup_path.is_symlink():
            raise ReleaseDeploymentError("No test Release backup is available")
        active_version = self._read_version(self._quirks_root)
        backup_version = self._read_version(self._backup_path)
        if active_version is None or backup_version is None:
            raise ReleaseDeploymentError("No test Release backup is available")

        stage_path = self._quirks_root / f".ezaiot-rollback-{uuid.uuid4().hex}"
        backup_files = self._package_files(self._backup_path)
        try:
            stage_path.mkdir()
            for relative_path in backup_files:
                target = self._quirks_root / relative_path
                if target.exists():
                    target.replace(stage_path / relative_path)
            (self._quirks_root / _VERSION_FILE).replace(stage_path / _VERSION_FILE)

            for relative_path in backup_files:
                (self._backup_path / relative_path).replace(
                    self._quirks_root / relative_path
                )
            (self._backup_path / _VERSION_FILE).replace(
                self._quirks_root / _VERSION_FILE
            )

            for relative_path in backup_files:
                staged_file = stage_path / relative_path
                if staged_file.exists():
                    staged_file.replace(self._backup_path / relative_path)
            (stage_path / _VERSION_FILE).replace(self._backup_path / _VERSION_FILE)

            return DeploymentState(
                installed_version=backup_version,
                backup_version=active_version,
                deployed_at=None,
                last_error=None,
            )
        except OSError as err:
            raise ReleaseDeploymentError("Unable to restore test Release backup") from err
        finally:
            if stage_path.exists():
                shutil.rmtree(stage_path)

    def _read_legacy_version(self) -> str | None:
        """Return the old subdirectory version only when it is a real directory."""
        if not self._legacy_path.exists():
            return None
        if not self._legacy_path.is_dir() or self._legacy_path.is_symlink():
            raise ReleaseDeploymentError("Legacy managed directory must not be a symbolic link")
        return self._read_version(self._legacy_path)

    def _assert_targets_are_managed(
        self,
        package_files: list[Path],
        previous_version: str | None,
        legacy_version: str | None,
    ) -> None:
        """Refuse to replace a root Quirk without an ezAIoT ownership marker."""
        if previous_version is not None:
            return
        for relative_path in package_files:
            if (self._quirks_root / relative_path).exists():
                raise ReleaseDeploymentError(
                    "Refusing to replace a root Quirk that is not ezAIoT-managed"
                )
        if self._legacy_path.exists() and legacy_version is None:
            raise ReleaseDeploymentError("Legacy managed directory has no version marker")

    def _replace_backup(self) -> None:
        """Create an empty local backup directory, removing only the old backup."""
        self._remove_backup()
        self._backup_path.mkdir()

    def _remove_backup(self) -> None:
        """Remove an existing ezAIoT backup directory after validating its type."""
        if not self._backup_path.exists():
            return
        if not self._backup_path.is_dir() or self._backup_path.is_symlink():
            raise ReleaseDeploymentError("Managed backup must not be a symbolic link")
        shutil.rmtree(self._backup_path)

    def _move_active_to_backup(self, package_files: list[Path]) -> None:
        """Move only incoming ezAIoT file names and the root version marker to backup."""
        for relative_path in package_files:
            target = self._quirks_root / relative_path
            if target.exists():
                target.replace(self._backup_path / relative_path)
        (self._quirks_root / _VERSION_FILE).replace(self._backup_path / _VERSION_FILE)

    def _activate(self, stage_path: Path, package_files: list[Path]) -> None:
        """Move staged files and their ownership marker into the Quirk root."""
        for relative_path in package_files:
            (stage_path / relative_path).replace(self._quirks_root / relative_path)
        (stage_path / _VERSION_FILE).replace(self._quirks_root / _VERSION_FILE)

    def _restore_backup(self, package_files: list[Path]) -> None:
        """Restore the active release after an activation failure."""
        for relative_path in package_files:
            target = self._quirks_root / relative_path
            if target.exists():
                target.unlink()
            backup_file = self._backup_path / relative_path
            if backup_file.exists():
                backup_file.replace(target)
        version_file = self._quirks_root / _VERSION_FILE
        if version_file.exists():
            version_file.unlink()
        (self._backup_path / _VERSION_FILE).replace(version_file)

    def _extract(self, package: bytes, stage_path: Path) -> None:
        """Extract bounded, regular root files below the staging directory."""
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
                if path.name in seen:
                    raise ReleaseDeploymentError("Duplicate test package file")
                seen.add(path.name)
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
                (stage_path / path).write_bytes(contents)

    @staticmethod
    def _package_files(directory: Path) -> list[Path]:
        """List flat package files, excluding the ezAIoT version marker."""
        return sorted(
            (Path(path.name) for path in directory.iterdir() if path.name != _VERSION_FILE),
            key=lambda path: path.name,
        )

    @staticmethod
    def _safe_path(info: zipfile.ZipInfo) -> Path:
        path = PurePosixPath(info.filename)
        if (
            not info.filename
            or "\\" in info.filename
            or path.is_absolute()
            or ".." in path.parts
            or path.name in {"", "."}
            or path.parent != PurePosixPath(".")
            or path.name == _VERSION_FILE
        ):
            raise ReleaseDeploymentError("Unsafe test package path")
        return Path(path.name)

    @staticmethod
    def _read_version(directory: Path) -> str | None:
        try:
            version = (directory / _VERSION_FILE).read_text(encoding="utf-8")
        except OSError:
            return None
        return version or None
