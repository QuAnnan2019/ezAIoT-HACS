"""Data structures shared by ezAIoT discovery and presentation."""

from dataclasses import dataclass
from enum import StrEnum


class CompatibilityState(StrEnum):
    """Compatibility state exposed by the integration."""

    SUPPORTED = "supported"
    NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True)
class SupportRecord:
    """Redacted information about a supported device."""

    ordinal: int
    manufacturer: str
    model: str
    entity_count: int


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """A redacted result produced from Home Assistant registries."""

    state: CompatibilityState
    records: tuple[SupportRecord, ...]

    @property
    def supported_count(self) -> int:
        """Return the number of exact-match supported devices."""
        return len(self.records)
