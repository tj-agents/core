import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "update_catalog_digests", ROOT / "scripts/update_catalog_digests.py"
)
CATALOG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CATALOG)


class CatalogVersionTests(unittest.TestCase):
    def test_matching_external_manifest_version_is_accepted(self) -> None:
        CATALOG.validate_package_version(
            {"id": "example/plugin", "version": "1.2.3"},
            {"version": "1.2.3"},
            "v1.2.3",
        )

    def test_stale_external_catalog_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "catalog version.*manifest version"):
            CATALOG.validate_package_version(
                {"id": "example/plugin", "version": "1.2.2"},
                {"version": "1.2.3"},
                "v1.2.3",
            )


if __name__ == "__main__":
    unittest.main()
