"""Contracts for redacted ZHA diagnostic helpers."""

from importlib.metadata import PackageNotFoundError
from types import SimpleNamespace

from custom_components.ezaiot import zha_diagnostics


def test_summary_hashes_ieee_and_reports_cluster_ids_only() -> None:
    """A diagnostic summary excludes raw addresses and cluster attributes."""
    endpoint = SimpleNamespace(
        in_clusters={6: object(), 64546: object()},
        out_clusters={25: object()},
    )
    device = SimpleNamespace(
        ieee="00:11:22:33:44:55:66:77",
        endpoints={0: SimpleNamespace(), 1: endpoint},
    )

    assert zha_diagnostics.summarize_zha_device(device) == {
        "ieee_hash": "74e831a01ddb",
        "endpoints": [
            {"id": 1, "in_clusters": [6, 64546], "out_clusters": [25]}
        ],
    }


def test_summary_accepts_missing_device_and_cluster_maps() -> None:
    """Unavailable ZHA data yields safe empty output."""
    assert zha_diagnostics.summarize_zha_device(None) is None
    device = SimpleNamespace(ieee=None, endpoints={1: SimpleNamespace()})
    assert zha_diagnostics.summarize_zha_device(device) == {
        "ieee_hash": None,
        "endpoints": [{"id": 1, "in_clusters": [], "out_clusters": []}],
    }


def test_environment_versions_handles_a_missing_zigpy_package(monkeypatch) -> None:
    """Missing package metadata does not prevent diagnostic export."""
    def missing_version(_: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(zha_diagnostics.metadata, "version", missing_version)

    versions = zha_diagnostics.environment_versions()

    assert isinstance(versions["python"], str)
    assert versions["zigpy"] is None
