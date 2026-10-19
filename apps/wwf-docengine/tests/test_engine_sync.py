"""The vendored engine must be byte-identical to the repository's pp-document-suite.

Canon revision of 09.10.2026 (Head of QC): the suite is the single source of the engine; the
copy under engine/ exists only because the image is built from this directory. Two diverged
lines are what produced different documents from the same Markdown (TEST_REPORT 2026-10-09,
defect 2). Refresh with engine/sync_from_suite.sh.
"""
import filecmp
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SUITE = HERE.parents[1] / "pp-document-suite"
ENGINE = HERE / "engine"


def _files(root: Path):
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


@pytest.mark.skipif(not SUITE.is_dir(), reason="pp-document-suite not in this checkout")
@pytest.mark.parametrize("sub", ["scripts", "assets", "references"])
def test_engine_matches_suite(sub):
    suite = [f for f in _files(SUITE / sub) if sub != "scripts" or f.suffix in (".py", ".sh", ".ps1")]
    assert _files(ENGINE / sub) == suite, f"engine/{sub} file list differs from pp-document-suite/{sub}"
    differ = [str(f) for f in suite if not filecmp.cmp(SUITE / sub / f, ENGINE / sub / f, shallow=False)]
    assert not differ, f"run engine/sync_from_suite.sh — differs: {differ}"


def test_manifest_records_the_engine_files():
    """engine/MANIFEST is what GET /engine/environment compares the image's engine against; a stale
    line would report every deployment as drifted (or hide a real drift)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("engine_env", HERE / "app" / "engine_env.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.manifest_hash() == mod.engine_hash(), "run engine/sync_from_suite.sh — engine/MANIFEST is stale"
