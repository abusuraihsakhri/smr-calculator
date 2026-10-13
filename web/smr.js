/* Dependency-free exact Poisson SMR arithmetic; runs in browsers and Node. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.SMR = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const lanczos = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.6150291621406, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];

  function logGamma(z) {
    if (z < 0.5) return Math.log(Math.PI) - Math.log(Math.sin(Math.PI * z)) - logGamma(1 - z);
    z -= 1;
    let x = lanczos[0];
    for (let i = 1; i < lanczos.length; i++) x += lanczos[i] / (z + i);
    const t = z + 7.5;
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
  }

  function gammaP(a, x) {
    if (!(a > 0) || x < 0) throw new RangeError('Invalid gamma parameters');
    if (x === 0) return 0;
    const factor = Math.exp(a * Math.log(x) - x - logGamma(a));
    if (x < a + 1) {
      let term = 1 / a, sum = term;
      for (let n = 1; n < 10000; n++) {
        term *= x / (a + n);
        sum += term;
        if (Math.abs(term) < Math.abs(sum) * 1e-14) return Math.min(1, Math.max(0, factor * sum));
      }
      throw new Error('Gamma series failed to converge');
    }
    let b = x + 1 - a, c = 1e300, d = 1 / (Math.abs(b) > 1e-300 ? b : 1e-300), h = d;
    for (let n = 1; n < 10000; n++) {
      const an = -n * (n - a);
      b += 2;
      d = an * d + b;
      if (Math.abs(d) < 1e-300) d = 1e-300;
      c = b + an / c;
      if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1 / d;
      const delta = d * c;
      h *= delta;
      if (Math.abs(delta - 1) < 1e-14) return Math.min(1, Math.max(0, 1 - factor * h));
    }
    throw new Error('Gamma fraction failed to converge');
  }

  function chiSquareQuantile(p, df) {
    if (!(p > 0 && p < 1) || !(df > 0)) throw new RangeError('Invalid quantile parameters');
    const a = df / 2;
    let low = 0, high = Math.max(1, df);
    while (gammaP(a, high / 2) < p) {
      high *= 2;
      if (!Number.isFinite(high)) throw new RangeError('Quantile overflow');
    }
    for (let n = 0; n < 110; n++) {
      const mid = (low + high) / 2;
      if (gammaP(a, mid / 2) < p) low = mid;
      else high = mid;
    }
    return (low + high) / 2;
  }

  function observedCount(raw) {
    if (raw === '' || raw === null || raw === undefined || typeof raw === 'boolean') {
      throw new RangeError('Observed deaths must be a nonnegative integer.');
    }
    const val = Number(raw);
    if (!Number.isSafeInteger(val) || val < 0 || val > 10000000) {
      throw new RangeError('Observed deaths must be an integer from 0 to 10,000,000.');
    }
    return val;
  }
  function expectedCount(raw) {
    if (raw === '' || raw === null || raw === undefined || typeof raw === 'boolean') {
      throw new RangeError('Expected deaths must be positive and finite.');
    }
    const val = Number(raw);
    if (!(val > 0) || !Number.isFinite(val)) {
      throw new RangeError('Expected deaths must be positive and finite.');
    }
    return val;
  }
  function calculate(observed, expected, confidenceLevel = 0.95) {
    const o = observedCount(observed), e = expectedCount(expected);
    if (!Number.isFinite(confidenceLevel) || !(confidenceLevel > 0 && confidenceLevel < 1)) {
      throw new RangeError('Confidence level must be between 0 and 1.');
    }
    const alpha = 1 - confidenceLevel;
    const lower = o === 0 ? 0 : chiSquareQuantile(alpha / 2, 2 * o) / (2 * e);
    const upper = chiSquareQuantile(1 - alpha / 2, 2 * (o + 1)) / (2 * e);
    const ratio = o / e;
    if (![ratio, lower, upper, o - e].every(Number.isFinite)) {
      throw new RangeError('Input magnitude produces a non-finite SMR or confidence limit.');
    }
    return {
      observed: o, expected: e, smr: ratio, smr_per_100: ratio * 100,
      ci_lower: lower, ci_upper: upper, confidence_level: confidenceLevel,
      excess_deaths: o - e, relative_difference_percent: (ratio - 1) * 100,
      method: 'Garwood exact Poisson (fixed expected count)'
    };
  }
  function validate(observed, expected) {
    return { observed: observedCount(observed), expected: expectedCount(expected) };
  }
  function aggregate(rows, confidenceLevel = 0.95) {
    if (!Array.isArray(rows) || !rows.length) throw new RangeError('At least one stratum is required.');
    let observed = 0, expected = 0;
    rows.forEach((row, i) => {
      try {
        observed += observedCount(row.observed);
        expected += expectedCount(row.expected);
      } catch (error) {
        throw new RangeError('Row ' + (i + 1) + ': ' + error.message);
      }
    });
    if (observed > 10000000) throw new RangeError('Total observed deaths exceed 10,000,000.');
    return { ...calculate(observed, expected, confidenceLevel), strata_count: rows.length };
  }
  return { calculate, aggregate, validate, chiSquareQuantile };
});
