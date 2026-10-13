"""Reference-value and validation tests for the SMR estimator."""
import math
import pytest

from smr_core import calculate_smr, calculate_smr_strata


@pytest.mark.parametrize(
    "observed,expected,smr,lower,upper",
    [
        (0, 10, 0, 0, 0.368888),
        (1, 1, 1, 0.0253178, 5.57164),
        (10, 8, 1.25, 0.5994, 2.299),
        (100, 80, 1.25, 1.017, 1.520),
    ],
)
def test_garwood_reference_values(observed, expected, smr, lower, upper):
    result = calculate_smr(observed, expected)
    assert result["smr"] == pytest.approx(smr)
    assert result["ci_lower"] == pytest.approx(lower, rel=0.003, abs=1e-6)
    assert result["ci_upper"] == pytest.approx(upper, rel=0.003)
    assert result["smr_per_100"] == pytest.approx(100 * smr)


def test_stratified_aggregation():
    rows = [{"observed": 4, "expected": 3.0}, {"observed": 6, "expected": 5.0}]
    result = calculate_smr_strata(rows)
    assert result["observed"] == 10
    assert result["expected"] == 8
    assert result["strata_count"] == 2
    assert result["smr"] == pytest.approx(1.25)
    assert result["excess_deaths"] == pytest.approx(2)


@pytest.mark.parametrize(
    "observed,expected",
    [(-1, 1), (1.2, 1), (True, 1), ("", 1), (2, 0), (1, -1),
     (1, float("inf")), (1, float("nan")), (1, 1e-320), (1, True)],
)
def test_reject_bad_counts(observed, expected):
    with pytest.raises(ValueError):
        calculate_smr(observed, expected)


@pytest.mark.parametrize("cl", [0, 1, -0.1, float("nan"), float("inf"), "95%"])
def test_reject_bad_confidence_level(cl):
    with pytest.raises(ValueError):
        calculate_smr(1, 1, cl)


def test_zero_and_empty_strata():
    with pytest.raises(ValueError):
        calculate_smr_strata([])
    with pytest.raises(ValueError):
        calculate_smr_strata([{"observed": 1}])
    with pytest.raises(ValueError):
        calculate_smr_strata([{"observed": 1, "expected": 0}])


def test_precision_for_large_count():
    result = calculate_smr(100_000, 100_000)
    assert result["ci_lower"] < 1 < result["ci_upper"]
    assert result["ci_upper"] - result["ci_lower"] < 0.02
