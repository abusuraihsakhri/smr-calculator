# SMR Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Standardized Mortality Ratio Calculator with clinical decision support functions:
- **MELD-Na Score**: Liver disease severity assessment (UNOS guidelines)
- **QTc Correction**: QT interval correction using Bazett's formula
- **BMI Z-Score**: Pediatric growth assessment with WHO reference
- **HbA1c Conversion**: Convert between HbA1c and estimated average glucose
- **APRI & FIB-4**: Liver fibrosis assessment scores
- **SMR Processing**: Batch CSV processing with clinical calculations

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Clinical Calculation Functions

- **`calculate_meld_na()`**: MELD-Na score for liver transplant priority
- **`calculate_qtc()`**: QTc interval correction (Bazett's formula)
- **`calculate_bmi_z()`**: BMI Z-score for pediatric growth charts
- **`convert_hba1c()`**: HbA1c ↔ eAG conversion (ADA formula)
- **`calculate_apri_fib4()`**: APRI and FIB-4 liver fibrosis scores
- **`assess_row()`**: Auto-detect calculation type from input data
- **`process_csv()`**: Batch process CSV files with clinical data

---

## 📐 Mathematical Formulations

### MELD-Na Score
```
MELD = 3.78*ln(bilirubin) + 11.2*ln(INR) + 9.57*ln(creatinine) + 6.43
MELD-Na = MELD + 1.32*(137-Na) - [0.033*MELD*(137-Na)]
Score bounded: 6-40 per UNOS guidelines
```

### QTc (Bazett's Formula)
```
QTc = QT / sqrt(RR in seconds)
RR = 60 / HR (if RR not provided)
```

### HbA1c to eAG Conversion
```
eAG (mg/dL) = 28.7 * HbA1c - 46.7
```

### APRI Score
```
APRI = (AST / AST_ULN) / platelets * 100
```

### FIB-4 Score
```
FIB-4 = (age * AST) / (platelets * sqrt(ALT))
```

---

## 💻 Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12
- pip (Python package manager)

### Setup
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/smr-calculator.git
cd smr-calculator

# Install dependencies
pip install fastapi uvicorn pydantic

# Or install with test dependencies
pip install -e ".[test]"
```

---

## 🚀 Usage

### 1. Command Line Interface

#### Single Calculation
```bash
# MELD-Na Score
python -m smr single --bili 2.0 --creat 1.5 --inr 1.2 --na 135

# QTc Correction
python -m smr single --qt 400 --hr 70

# BMI Z-Score
python -m smr single --json '{"weight_kg": 70, "height_cm": 175, "age_months": 60, "sex": "M"}'
```

#### Batch CSV Processing
```bash
python -m smr batch --input sample.csv --output results.csv
```

### 2. Interactive CLI
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
python cli.py chat "Explain MELD-Na scoring"
python cli.py verify-audit
```

### 3. REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

API Endpoints:
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /api/audit` - Submit task for evaluation
- `POST /api/chat` - Supervisory chat
- `GET /api/audit/logs` - Audit trail

### 4. Docker Deployment
```bash
# Build and run
docker build -t smr-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret smr-calculator

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret docker-compose up
```

---

## 📊 Input Data Schema

### CSV Format for Batch Processing

| Field | Description | Used By |
|:------|:------------|:--------|
| `bilirubin` | Bilirubin level (mg/dL) | MELD-Na |
| `creatinine` | Creatinine level (mg/dL) | MELD-Na |
| `inr` | International Normalized Ratio | MELD-Na |
| `sodium` | Sodium level (mEq/L) | MELD-Na |
| `qt_ms` | QT interval (ms) | QTc |
| `hr_bpm` | Heart rate (bpm) | QTc |
| `weight_kg` | Weight in kilograms | BMI-Z |
| `height_cm` | Height in centimeters | BMI-Z |
| `hba1c_percent` | HbA1c percentage | HbA1c |
| `ast_u_l` | AST level (U/L) | APRI/FIB-4 |
| `alt_u_l` | ALT level (U/L) | FIB-4 |
| `platelets_109` | Platelet count (10^9/L) | APRI/FIB-4 |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
* **Configurable Secret Key:** Set `AUDIT_SECRET_KEY` environment variable for production (no hardcoded defaults)
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational metrics

### Security Configuration
```bash
# Set audit secret key (required for production)
export AUDIT_SECRET_KEY="your-secure-random-key"

# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🧪 Testing & Verification

### Run All Tests
```bash
pytest -v
```

### Run Specific Test Suites
```bash
# Clinical calculation tests
pytest tests/test_smr_functions.py -v

# Enterprise agent tests
pytest tests/test_smr_calculator.py -v

# Enrichment engine tests
pytest tests/test_enrichment.py -v
```

### Run Simulation Benchmark
```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build
docker build -t smr-calculator .

# Run with custom secret
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") smr-calculator

# Docker Compose
AUDIT_SECRET_KEY=your-secret docker-compose up
```

---

## 📁 Project Structure

```
smr-calculator/
├── smr.py                 # Core clinical calculation functions
├── cli.py                 # Command line interface
├── simulator.py           # High-throughput testing simulator
├── enrichment.py          # Feature enrichment engines
├── agents/                # Enterprise agent framework
│   ├── __init__.py
│   ├── base.py           # Security, PHI guard, HMAC audit
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Task orchestrator
│   ├── workers.py        # Specialized evaluation workers
│   ├── api.py            # FastAPI REST server
│   ├── llm_factory.py    # LLM provider factory
│   ├── learning.py       # Bayesian calibration engine
│   ├── metrics.py        # Prometheus metrics
│   └── streamer.py       # WebSocket telemetry
├── tests/                # Test suite
│   ├── test_smr_calculator.py
│   ├── test_smr_functions.py
│   └── test_enrichment.py
├── web/                  # Web interface
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
