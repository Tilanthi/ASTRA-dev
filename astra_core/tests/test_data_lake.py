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


def test_round_robin_cycles_productive_datasets():
    """The supervisor's per-episode picker must cycle through all productive niches."""
    import tempfile
    from astra_core.scientific_discovery.evolved_analysis import mine_rotation as mr
    with tempfile.TemporaryDirectory() as td:
        orig = mr._ROUND_ROBIN_POINTER
        mr._ROUND_ROBIN_POINTER = Path(td) / "pointer.json"
        try:
            ds = productive_datasets()
            assert len(ds) >= 1
            picks = [mr._round_robin_pick(ds).name for _ in range(len(ds))]
            assert set(picks) == {d.name for d in ds}, \
                f"round-robin should cover all productive niches; got {picks}"
            assert mr._round_robin_pick(ds).name == picks[0]  # wraps to first
        finally:
            mr._ROUND_ROBIN_POINTER = orig


def test_correlation_seeds_finds_strong_nontrivial():
    """Phase 1a: seeds surface the strongest non-trivial real correlations."""
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)

        def _fetch():
            import numpy as np
            rng = np.random.default_rng(0)
            x = rng.normal(size=300)
            y = 0.7 * x + 0.5 * rng.normal(size=300)   # strong-but-nontrivial
            z = rng.normal(size=300)                    # uncorrelated
            return pd.DataFrame({"x": x, "y": y, "z": z})
        ds = Dataset(name="corr_test", description="d", columns=["x", "y", "z"],
                     source="test", fetcher=_fetch, cache_basename="corr_test.csv")
        register_dataset(ds)
        fetch_and_cache("corr_test")
        seeds = data_lake.correlation_seeds("corr_test", top_k=5)
        # x-y is the strongest pair; z doesn't appear strongly
        assert any({a, b} == {"x", "y"} for a, b, _ in seeds)
        assert all(abs(r) <= 0.95 for _, _, r in seeds)   # rmax filter holds


def test_correlation_seeds_defensive_on_missing():
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)
        register_dataset(Dataset(name="nocache_corr", description="d", columns=["a"],
                                 source="t", cache_basename="nocache_corr.csv"))
        assert data_lake.correlation_seeds("nocache_corr") == []  # no cache -> [], not raise


def test_correlation_seeds_excludes_concatenated_band_colours():
    """Bug: a pre-computed colour whose name has no dash (e.g. WISE 'w1w2') was
    misclassified as a science column, so colour<->colour pairs that share bands
    (algebraically coupled -> trivial) leaked into the seeds. Such pairs must be
    dropped."""
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)

        def _fetch():
            import numpy as np
            rng = np.random.default_rng(1)
            flux = rng.normal(50, 5, 400)          # common flux driver -> bands correlated
            temp = rng.normal(0, 1, 400)           # a real colour driver
            w1 = flux + temp + rng.normal(0, 0.3, 400)
            w2 = flux + 0.5 * temp + rng.normal(0, 0.3, 400)
            w3 = flux + 0.2 * temp + rng.normal(0, 0.3, 400)
            return pd.DataFrame({
                "w1": w1, "w2": w2, "w3": w3,
                "w1w2": w1 - w2,                   # pre-computed colour, no dash (like WISE cache)
                "mass": 0.6 * temp + rng.normal(0, 0.3, 400),  # genuine science column
            })
        ds = Dataset(name="wise_bug", description="d",
                     columns=["w1", "w2", "w3", "w1w2", "mass"],
                     source="test", fetcher=_fetch, cache_basename="wise_bug.csv")
        register_dataset(ds)
        fetch_and_cache("wise_bug")
        seeds = data_lake.correlation_seeds("wise_bug", top_k=12)
        colour_feats = {"w1-w2", "w1-w3", "w2-w3", "w1w2"}
        for a, b, _ in seeds:
            assert not (a in colour_feats and b in colour_feats), \
                f"trivial colour<->colour pair leaked: {a} vs {b}"


def test_correlation_seeds_surfaces_residual_signals():
    """The strongest pairwise correlations ARE the textbook ones (filtered or
    unhelpful). Seeds should ALSO surface RESIDUAL structure -- a relation that
    appears only after removing a science column's dominant predictor -- a
    genuinely non-obvious starting point the proposer can build on."""
    with tempfile.TemporaryDirectory() as td:
        _fresh_lake(td)

        def _fetch():
            import numpy as np
            rng = np.random.default_rng(2)
            u = rng.normal(0, 1, 500)
            g = u + rng.normal(0, 0.1, 500)
            feh = rng.normal(0, 1, 500)            # independent science column
            # z_spec is dominated by u (~r0.95 -> filtered by rmax) but also carries
            # a feh signal visible ONLY in the residual after removing u.
            z_spec = 3.0 * u + 1.0 * feh + rng.normal(0, 0.2, 500)
            return pd.DataFrame({"u": u, "g": g, "z_spec": z_spec, "feh": feh})
        ds = Dataset(name="resid_test", description="d",
                     columns=["u", "g", "z_spec", "feh"],
                     source="test", fetcher=_fetch, cache_basename="resid_test.csv")
        register_dataset(ds)
        fetch_and_cache("resid_test")
        seeds = data_lake.correlation_seeds("resid_test", top_k=10)
        assert any(a.startswith("resid") and b == "feh" for a, b, _ in seeds), \
            f"no residual seed surfacing the z_spec~feh signal; got {seeds}"


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
