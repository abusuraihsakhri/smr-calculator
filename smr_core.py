"""Standardized mortality ratio with Garwood (exact Poisson) confidence limits.

The expected count is treated as fixed. This is an indirect-standardization
calculation, not a confidence interval for a reference population's rate.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def _gamma_p(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x); a > 0, x >= 0."""
    if a <= 0 or x < 0:
        raise ValueError("Invalid gamma parameters")
    if x == 0:
        return 0.0
    log_term = a * math.log(x) - x - math.lgamma(a)
    if x < a + 1:
        term = 1.0 / a
        total = term
        for i in range(1, 10000):
            term *= x / (a + i)
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        else:
            raise ArithmeticError("Gamma series did not converge")
        return min(1.0, max(0.0, total * math.exp(log_term)))

    # Continued fraction for Q(a,x) = 1 - P(a,x).
    tiny = 1e-300
    b = x + 1 - a
    c = 1.0 / tiny
    d = 1.0 / (b if abs(b) > tiny else tiny)
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    else:
        raise ArithmeticError("Gamma continued fraction did not converge")
    return min(1.0, max(0.0, 1.0 - math.exp(log_term) * h))


def _chi2_quantile(probability: float, df: int) -> float:
    if not 0 < probability < 1 or df <= 0:
        raise ValueError("Invalid chi-square quantile parameters")
    a = df / 2.0
    low, high = 0.0, max(1.0, float(df))
    while _gamma_p(a, high / 2.0) < probability:
        high *= 2.0
        if not math.isfinite(high):
            raise ArithmeticError("Chi-square quantile overflow")
    for _ in range(110):
        mid = (low + high) / 2.0
        if _gamma_p(a, mid / 2.0) < probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _count(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("Observed deaths must be a nonnegative integer")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Observed deaths must be a nonnegative integer") from exc
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError("Observed deaths must be a nonnegative integer")
    if number > 10_000_000:
        raise ValueError("Observed deaths exceed the supported maximum (10,000,000)")
    return int(number)


def _expected(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("Expected deaths must be positive and finite")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Expected deaths must be positive and finite") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError("Expected deaths must be positive and finite")
    return number


def calculate_smr(
    observed: int | float | str,
    expected: int | float | str,
    confidence_level: float = 0.95,
) -> dict:
    """Compute observed/expected SMR and two-sided exact Poisson CI.

    Returns the ratio (reference 1), its scale-of-100 representation
    (reference 100), observed-minus-expected, and the interval bounds.
    """
    o, e = _count(observed), _expected(expected)
    if not isinstance(confidence_level, (float, int)) or isinstance(confidence_level, bool):
        raise ValueError("Confidence level must be between 0 and 1")
    cl = float(confidence_level)
    if not math.isfinite(cl) or not 0 < cl < 1:
        raise ValueError("Confidence level must be between 0 and 1")
    alpha = 1 - cl
    lower = _chi2_quantile(alpha / 2, 2 * o) / (2 * e) if o else 0.0
    upper = _chi2_quantile(1 - alpha / 2, 2 * (o + 1)) / (2 * e)
    ratio = o / e
    if not all(math.isfinite(x) for x in (ratio, lower, upper, o - e)):
        raise ValueError("Input magnitude produces a non-finite SMR or confidence limit")
    return {
        "observed": o,
        "expected": e,
        "smr": ratio,
        "smr_per_100": ratio * 100,
        "ci_lower": lower,
        "ci_upper": upper,
        "confidence_level": cl,
        "excess_deaths": o - e,
        "relative_difference_percent": 100 * (ratio - 1),
        "method": "Garwood exact Poisson (fixed expected count)",
    }


def calculate_smr_strata(
    strata: Iterable[Mapping[str, object]], confidence_level: float = 0.95
) -> dict:
    """Aggregate observed and expected counts before calculating an SMR.

    Each stratum needs an observed nonnegative integer and a positive
    expected count, which may be estimated as population-at-risk ×
    reference stratum-specific mortality rate.
    """
    total_observed = 0
    total_expected = 0.0
    count = 0
    for count, row in enumerate(strata, 1):
        if "observed" not in row or "expected" not in row:
            raise ValueError(f"Stratum {count} requires observed and expected")
        total_observed += _count(row["observed"])
        total_expected += _expected(row["expected"])
    if count == 0:
        raise ValueError("At least one stratum is required")
    output = calculate_smr(total_observed, total_expected, confidence_level)
    output["strata_count"] = count
    return output
