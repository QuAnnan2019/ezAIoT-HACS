"""Immutable types for trusted Quirk Release processing."""

from dataclasses import dataclass
from enum import StrEnum


class ReleaseStatus(StrEnum):
    """The finite release states safe for presentation."""

    NO_RELEASE = "no_release"
    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    CHECKING = "checking"
    INSTALLING = "installing"
    ROLLING_BACK = "rolling_back"
    VERIFICATION_FAILED = "verification_failed"


@dataclass(frozen=True, slots=True)
class PackageFile:
    """One file allowed in a signed release package."""

    path: str
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    """An asset selected from the fixed GitHub Release API response."""

    asset_id: int
    name: str
    size: int
    api_url: str


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    """Verified metadata describing one eligible Quirk package."""

    version: str
    platform: str
    manufacturer: str
    model: str
    package_name: str
    package_size: int
    package_sha256: str
    files: tuple[PackageFile, ...]
    release_notes: str
    restart_required: bool


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    """A verified manifest with its fixed-origin Release assets."""

    manifest: ReleaseManifest
    package: ReleaseAsset
    release_url: str


@dataclass(frozen=True, slots=True)
class DeploymentState:
    """Persisted state for the ezAIoT-managed Quirk directory."""

    installed_version: str | None
    backup_version: str | None
    deployed_at: str | None
    last_error: str | None
