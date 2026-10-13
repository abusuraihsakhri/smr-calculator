'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {calculate, aggregate} = require('../web/smr.js');

const near = (a, b, tol = 1e-5) => assert.ok(Math.abs(a - b) < tol, a + ' ≠ ' + b);
test('Garwood exact Poisson reference values', () => {
  const zero = calculate(0, 10);
  near(zero.ci_lower, 0);
  near(zero.ci_upper, 0.36888794541139);
  const one = calculate(1, 1);
  near(one.ci_lower, 0.02531780798429);
  near(one.ci_upper, 5.5716433909389);
  const ten = calculate(10, 8);
  near(ten.smr, 1.25);
  near(ten.ci_lower, 0.59942358701655);
  near(ten.ci_upper, 2.29879450525222);
  const hundred = calculate(100, 80);
  near(hundred.ci_lower, 1.017049890636539);
  near(hundred.ci_upper, 1.520334922405329);
});
test('aggregated SMR uses sums, not average stratum SMRs', () => {
  const result = aggregate([{observed: 4, expected: 3}, {observed: 6, expected: 5}]);
  near(result.smr, 1.25);
  assert.equal(result.strata_count, 2);
  assert.equal(result.excess_deaths, 2);
});
test('invalid inputs are not coerced to zeros', () => {
  for (const [o,e] of [[-1,1],[1.5,1],[1,0],[1,-1],['',1],[true,1],[1,''],[0,Infinity],[1,1e-320]]) {
    assert.throws(() => calculate(o,e));
  }
  assert.deepEqual(require('../web/smr.js').validate('2', '3.5'), {observed: 2, expected: 3.5});
  assert.throws(() => aggregate([]));
  assert.throws(() => aggregate([{observed:2,expected:0}]));
  assert.throws(() => calculate(1, 1, 0));
  assert.throws(() => calculate(1, 1, 1));
});
test('large count and confidence options', () => {
  const result = calculate(100000, 100000, 0.99);
  assert.ok(result.ci_lower < 1);
  assert.ok(result.ci_upper > 1);
  assert.ok(result.ci_upper - result.ci_lower < 0.02);
});
