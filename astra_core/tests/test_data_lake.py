"""Tests for the data lake (Sub-project C): registry, cache, split, prompt.

No network — uses synthetic datasets with dummy fetchers and redirects the cache
dir to a temp path. The real fetchers (SDSS/Gaia) are exercised by the live
validation step, not here.

Run: python3 astra_core/tests/test_data_lake.py
"""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import data_lake  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis.data_lake import (  # noqa: E402
    Dataset, register_dataset, fetch_and_cache, load_dataframe,
    load_split, task_system_for, productive_datasets,
)


def _fresh_lake(tmpdir):
    data_lake.LAKE_DIR = Path(tmpdir)  # redirect cache to temp for isolation
    return data_lake.LAKE_DIR


def _make_dummy_dataset(name):
    def _fetch():
        return pd.DataFrame({"a": [1.0, 2, 3, 4, 5, 6], "b": [2.0, 4, 6, 8, 10, 12]})
    ds = Dataset(name=name, description="dummy dataset", columns=["a", "b"],
                 source="test", fetcher=_fetch, cache_basename=f"{name}.csv")
    register_dataset(ds)
    return ds


def test_registry_has_real_datasets():
    names = {d.name for d in data_lake.list_datasets()}
    assert {"sdss_stars", "sdss_qso", "sdss_galaxy_extended", "gaia_nearby"} <= names


def test_fetch_and_cache_writes_csv_and_manifest():
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)
        ds = _make_dummy_dataset("dummy_cache")
        cache = fetch_and_cache(ds.name)
        assert cache.exists()
        assert ds.manifest_path().exists()
        m = json.loads(ds.manifest_path().read_text())
        assert m["n_rows"] == 6 and "csv_sha1" in m


def test_fetch_uses_cache_on_second_call():
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)
        ds = _make_dummy_dataset("dummy_cached2")
        p1 = fetch_and_cache(ds.name)

        def _boom():
            raise RuntimeError("should not refetch")
        ds.fetcher = _boom  # would blow up if cache weren't used
        p2 = fetch_and_cache(ds.name)
        assert p1 == p2


def test_load_dataframe_and_split_shapes():
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)
        ds = _make_dummy_dataset("dummy_split")
        fetch_and_cache(ds.name)
        df = load_dataframe(ds.name)
        assert list(df.columns) == ["a", "b"] and len(df) == 6
        splits = load_split(ds.name, seed=1)
        assert set(splits) == {"train", "eval", "test"}
        total = splits["train"].shape[0] + splits["eval"].shape[0] + splits["test"].shape[0]
        assert total == 6


def test_unknown_dataset_raises():
    try:
        fetch_and_cache("definitely_not_a_real_dataset_xyz")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_load_without_cache_raises():
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)
        ds = _make_dummy_dataset("dummy_nocache")
        try:
            load_dataframe(ds.name)
            assert False, "expected FileNotFoundError"
        except FileNotFoundError:
            pass


def test_task_system_for_describes_columns():
    ts = task_system_for("gaia_nearby")
    assert ts and "parallax" in ts and "bp_rp" in ts
    assert task_system_for("nonexistent_dataset") is None


def test_productive_datasets_exclude_textbook_saturated():
    """Lever (b): stars/gaia are textbook-saturated and skipped by default."""
    names = {ds.name for ds in productive_datasets()}
    assert "sdss_galaxy_extended" in names and "sdss_qso" in names
    assert "sdss_stars" not in names      # HR-diagram-dominated
    assert "gaia_nearby" not in names     # 100% known in pilots


def test_task_system_for_includes_niche_hint():
    """Niche hints focus the proposer on the relation types that yielded novelty."""
    ts_qso = task_system_for("sdss_qso")
    assert ts_qso and "colour×redshift" in ts_qso           # niche hint present
    ts_gal = task_system_for("sdss_galaxy_extended")
    assert ts_gal and "concentration-index" in ts_gal


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as e:
                failed += 1
                print(f"FAIL  {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
