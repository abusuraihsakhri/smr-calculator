# SMR Calculator

An observed-to-expected standardized mortality ratio (SMR) estimator for epidemiology and public-health analyses. The primary calculator runs entirely in a web browser without Python, a backend, or external JavaScript dependencies.

## Features

- Computes indirect-standardization **SMR = observed / expected** (reference 1) and its ×100 representation (reference 100).
- **90%, 95%, or 99% exact Poisson (Garwood) confidence intervals**, treating the expected count as fixed.
- Excess deaths (observed minus expected) and percentage difference from expectation.
- Stratified CSV input with required **observed** and **expected** columns, optional **stratum** column, aggregate results, previews and downloadable output.
- Python functions, CLI, FastAPI endpoint, and regression tests.

The browser calculator is at [web/index.html](web/index.html). Open it directly or serve the web directory on any static HTTP server. A GitHub Pages workflow publishes that directory from the **master** branch. Whether the public URL is live depends on repository Pages configuration and a successful deployment.

## Statistical method

Given observed deaths O and expected deaths E > 0:

SMR = O / E; excess deaths = O − E.

For two-sided confidence level 1 − α, the Garwood exact Poisson limits are:

- Lower = 0 when O = 0, otherwise χ²(α/2, 2O) / (2E).
- Upper = χ²(1 − α/2, 2(O+1)) / (2E).

For indirect standardization, expected deaths are normally the sum of stratum-specific population or person-time multiplied by the corresponding reference rates. **Expected counts must already be calculated and supplied.** Observed counts must be nonnegative integers; expected counts must be positive and finite.

The calculation assumes Poisson-distributed observed counts and fixed expected counts. It does not propagate uncertainty in reference rates or account for confounding and selection. An SMR above 1 means observed mortality exceeds that expected from the chosen reference rates, but it is not evidence of causation. See [Liddell (1984)](https://pmc.ncbi.nlm.nih.gov/articles/PMC1052324/) for the exact chi-square/Poisson method.

## Browser usage

1. Open **web/index.html** in current Chrome, Firefox, Safari, or Edge.
2. Enter observed and expected deaths, choose a confidence level, and select **Calculate SMR**.
3. For stratified analysis, upload a CSV (2 MB limit, 10,000 data rows max) or paste CSV text and choose **Analyze strata**.
4. Download the overall and per-stratum results via **Download results CSV**.

Example input:

~~~csv
stratum,observed,expected
Age 45-64,12,10.5
Age 65+,33,25.5
~~~

**Privacy:** Browser CSV parsing, calculation and download remain on the client. The static app makes no API requests and stores no data in browser storage. Do not submit identifiable data to the legacy audit API: a pattern-matching identifier guard is not comprehensive de-identification or a HIPAA-compliance guarantee.

## Python CLI

Requires Python 3.10+. Install in a checkout:

~~~bash
python -m pip install -e ".[test]"
python -m smr smr --observed 45 --expected 36 --confidence 0.95
python -m smr single --json '{"observed":45,"expected":36}'
python -m smr batch --input sample_smr.csv --output results.csv
~~~

Python API:

~~~python
from smr_core import calculate_smr, calculate_smr_strata

result = calculate_smr(45, 36)
stratified = calculate_smr_strata([
    {"observed": 12, "expected": 10.5},
    {"observed": 33, "expected": 25.5},
])
~~~

## Optional FastAPI server

~~~bash
python cli.py serve --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/smr -H 'Content-Type: application/json' \
  -d '{"observed":45,"expected":36,"confidence_level":0.95}'
~~~

The server serves the browser interface at http://127.0.0.1:8000/ and retains the existing audit, chat, health, and metrics endpoints. The audit trail is **in-memory**, not a persistent compliance-grade ledger. Docker users must explicitly set a strong **AUDIT_SECRET_KEY** before running Docker Compose.

Legacy clinical utilities (MELD-Na, QTc, HbA1c/eAG, APRI, FIB-4) and audit CLI commands are retained for compatibility. The former generic **calculate_score** is a demonstration, *not* an SMR or clinically validated score. The historical pediatric BMI-Z estimate is a simplified, unvalidated approximation, **not** a WHO LMS reference score. The legacy chat is a deterministic mock, not an actual clinical decision-support service.

## Testing

~~~bash
python -m pip install -e ".[test]"
python -m pytest -q
node --test tests/test_smr_js.cjs
node --check web/smr.js
node --check web/app.js
python -m compileall -q smr.py smr_core.py agents
~~~

CI runs the Python test suite against versions 3.10–3.12 and the browser mathematics tests using Node.js 22. Browser execution requires no Pyodide, Python runtime, or backend.

**License:** [MIT](LICENSE).
