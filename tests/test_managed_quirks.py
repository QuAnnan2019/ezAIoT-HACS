"""Contracts for the exact device signatures in an ezAIoT Release."""

import json

import pytest

from custom_components.ezaiot.managed_quirks import (
    CATALOG_FILE_NAME,
    ManagedQuirkCatalogError,
    parse_catalog,
)


def _catalog(quirks: list[dict[str, str]]) -> bytes:
    return json.dumps({"schema_version": 1, "quirks": quirks}).encode()


def test_catalog_accepts_exact_two_quirk_release() -> None:
    catalog = parse_catalog(
        _catalog(
            [
                {
                    "file": "rti_tek_etrv_zb01.py",
                    "manufacturer": "Rti-Tek",
                    "model": "eTRV-ZB01",
                },
                {
                    "file": "rti_tek_sthzb.py",
                    "manufacturer": "Rti-Tek",
                    "model": "STHZB",
                },
            ]
        ),
        {"rti_tek_etrv_zb01.py", "rti_tek_sthzb.py", CATALOG_FILE_NAME},
    )

    assert catalog.files == ("rti_tek_etrv_zb01.py", "rti_tek_sthzb.py")
    assert [(item.manufacturer, item.model) for item in catalog.quirks] == [
        ("Rti-Tek", "eTRV-ZB01"),
        ("Rti-Tek", "STHZB"),
    ]


@pytest.mark.parametrize(
    ("quirks", "package_files"),
    [
        (
            [
                {
                    "file": "rti_tek_sthzb.py",
                    "manufacturer": "Rti-Tek",
                    "model": "STHZB",
                },
                {
                    "file": "rti_tek_sthzb.py",
                    "manufacturer": "Rti-Tek",
                    "model": "STHZB-Preview",
                },
            ],
            {"rti_tek_sthzb.py", CATALOG_FILE_NAME},
        ),
        (
            [
                {
                    "file": "../rti_tek_sthzb.py",
                    "manufacturer": "Rti-Tek",
                    "model": "STHZB",
                },
            ],
            {"rti_tek_sthzb.py", CATALOG_FILE_NAME},
        ),
        (
            [
                {
                    "file": "rti_tek_sthzb.py",
                    "manufacturer": "Rti-Tek",
                    "model": "STHZB",
                },
            ],
            {"rti_tek_sthzb.py", "unexpected.py", CATALOG_FILE_NAME},
        ),
    ],
)
def test_catalog_rejects_duplicate_unsafe_or_mismatched_files(
    quirks: list[dict[str, str]], package_files: set[str]
) -> None:
    with pytest.raises(ManagedQuirkCatalogError):
        parse_catalog(_catalog(quirks), package_files)


def test_catalog_rejects_malformed_schema() -> None:
    with pytest.raises(ManagedQuirkCatalogError):
        parse_catalog(b'{"schema_version": 2, "quirks": []}', {CATALOG_FILE_NAME})
