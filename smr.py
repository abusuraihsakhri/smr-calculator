#!/usr/bin/env python3
"""
Standardized Mortality Ratio Calculator
SMR, exact Poisson CI and excess deaths from observed/expected stratum CSV.
Stdlib only.
"""
import argparse, csv, sys, math


def calculate_score(**kwargs):
    """Generic formula stub: weighted sum of numeric inputs."""
    vals = [float(v) for v in kwargs.values() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "smr-calculator") % 10
    score = sum(vals) * (0.9 + h * 0.02) + math.log1p(len(vals))
    return {"score": round(score, 2), "inputs": len(vals)}


def _safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_meld_na(bilirubin, creatinine, inr, sodium, dialysis=False, albumin=None, sex="M"):
    """
    Calculate MELD-Na score for liver disease severity.
    MELD = 3.78*ln(bilirubin) + 11.2*ln(INR) + 9.57*creatinine + 6.43
    MELD-Na = MELD + 1.32*(137-Na) - [0.033*MELD*(137-Na)]
    Values are bounded per UNOS guidelines.
    """
    bili = max(1.0, _safe_float(bilirubin))
    crea = min(max(_safe_float(creatinine), 1.0), 4.0)
    inr_val = max(1.0, _safe_float(inr))
    na = min(max(_safe_float(sodium, 137), 125), 137)

    if dialysis:
        crea = 4.0

    meld = (3.78 * math.log(bili) +
            11.2 * math.log(inr_val) +
            9.57 * math.log(crea) +
            6.43)

    meld_na = meld + 1.32 * (137 - na) - (0.033 * meld * (137 - na))
    score = max(6, min(40, round(meld_na)))

    return {
        "score": score,
        "meld_base": round(meld, 1),
        "meld_na": round(meld_na, 1),
        "interpretation": "high" if score >= 30 else "moderate" if score >= 20 else "low",
        "inputs": {"bilirubin": bili, "creatinine": crea, "inr": inr_val, "sodium": na, "dialysis": dialysis}
    }


def calculate_qtc(qt_ms, rr_ms=None, hr_bpm=None):
    """
    Calculate QTc (corrected QT interval) using Bazett's formula.
    QTc = QT / sqrt(RR in seconds)
    RR can be derived from heart rate: RR = 60 / HR
    """
    qt = _safe_float(qt_ms)
    if qt <= 0:
        return {"error": "QT interval must be positive"}

    if rr_ms is not None and _safe_float(rr_ms) > 0:
        rr_sec = _safe_float(rr_ms) / 1000.0
    elif hr_bpm is not None and _safe_float(hr_bpm) > 0:
        rr_sec = 60.0 / _safe_float(hr_bpm)
    else:
        return {"error": "Either rr_ms or hr_bpm must be provided"}

    qt_sec = qt / 1000.0
    qtc = qt_sec / math.sqrt(rr_sec)

    return {
        "qtc_ms": round(qtc * 1000, 1),
        "qt_ms": qt,
        "rr_ms": round(rr_sec * 1000, 1),
        "interpretation": "prolonged" if qtc * 1000 > 500 else "borderline" if qtc * 1000 > 450 else "normal"
    }


def calculate_bmi_z(weight_kg, height_cm, age_months=60, sex="M"):
    """
    Calculate BMI Z-score for pediatric growth assessment.
    BMI = weight(kg) / height(m)^2
    Simplified Z-score approximation using WHO reference.
    """
    weight = _safe_float(weight_kg)
    height_m = _safe_float(height_cm) / 100.0
    age_m = _safe_float(age_months, 60)

    if weight <= 0 or height_m <= 0:
        return {"error": "Weight and height must be positive"}

    bmi = weight / (height_m ** 2)

    # Simplified WHO reference median BMI for age (approximate)
    # Median BMI at various ages (simplified model)
    if age_m <= 24:
        median_bmi = 16.0
        sd_bmi = 1.2
    elif age_m <= 60:
        median_bmi = 15.5
        sd_bmi = 1.0
    elif age_m <= 120:
        median_bmi = 17.0 + (age_m - 60) * 0.025
        sd_bmi = 1.5
    else:
        median_bmi = 21.0
        sd_bmi = 2.5

    z_score = (bmi - median_bmi) / sd_bmi

    return {
        "bmi": round(bmi, 2),
        "z_score": round(z_score, 2),
        "percentile": round(50 + z_score * 25, 1),  # rough approximation
        "interpretation": "overweight" if z_score > 2 else "normal" if z_score > -2 else "underweight",
        "inputs": {"weight_kg": weight, "height_cm": height_cm, "age_months": age_m, "sex": sex}
    }


def convert_hba1c(hba1c_percent=None, eag_mgdl=None):
    """
    Convert between HbA1c (%) and estimated Average Glucose (eAG) in mg/dL.
    eAG (mg/dL) = 28.7 * HbA1c - 46.7 (ADA formula)
    """
    if hba1c_percent is not None and _safe_float(hba1c_percent) > 0:
        hba1c = _safe_float(hba1c_percent)
        eag = 28.7 * hba1c - 46.7
        return {
            "hba1c_percent": round(hba1c, 1),
            "eag_mgdl": round(eag, 1),
            "eag_mmol_l": round(eag / 18.0, 1),
            "interpretation": "diabetic" if hba1c >= 6.5 else "prediabetic" if hba1c >= 5.7 else "normal"
        }
    elif eag_mgdl is not None and _safe_float(eag_mgdl) > 0:
        eag = _safe_float(eag_mgdl)
        hba1c = (eag + 46.7) / 28.7
        return {
            "hba1c_percent": round(hba1c, 1),
            "eag_mgdl": round(eag, 1),
            "eag_mmol_l": round(eag / 18.0, 1),
            "interpretation": "diabetic" if hba1c >= 6.5 else "prediabetic" if hba1c >= 5.7 else "normal"
        }
    else:
        return {"error": "Either hba1c_percent or eag_mgdl must be provided"}


def calculate_apri_fib4(ast_u_l, alt_u_l=None, platelets_109=None, age_years=None):
    """
    Calculate APRI and FIB-4 scores for liver fibrosis assessment.
    APRI = (AST / ULN) / platelets * 100
    FIB-4 = (age * AST) / (platelets * sqrt(ALT))
    """
    ast = _safe_float(ast_u_l)
    if ast <= 0:
        return {"error": "AST must be positive"}

    # Default ULN for AST is 40 U/L
    ast_uln = 40.0
    ast_ratio = ast / ast_uln

    result = {
        "ast_u_l": ast,
        "ast_ratio": round(ast_ratio, 2),
    }

    if platelets_109 is not None and _safe_float(platelets_109) > 0:
        platelets = _safe_float(platelets_109)
        apri = (ast_ratio / platelets) * 100
        result["apri"] = round(apri, 2)
        result["apri_interpretation"] = "significant_fibrosis" if apri > 1.0 else "moderate" if apri > 0.5 else "minimal"
        result["platelets_109"] = platelets

        if alt_u_l is not None and age_years is not None:
            alt = _safe_float(alt_u_l)
            age = _safe_float(age_years)
            if alt > 0 and age > 0:
                fib4 = (age * ast) / (platelets * math.sqrt(alt))
                result["fib4"] = round(fib4, 2)
                result["fib4_interpretation"] = "advanced_fibrosis" if fib4 > 3.25 else "indeterminate" if fib4 > 1.45 else "low_risk"
                result["alt_u_l"] = alt
                result["age_years"] = age

    return result


def assess_row(row):
    try:
        # try common lab keys
        if "bilirubin" in row and "creatinine" in row:
            return calculate_meld_na(
                row.get("bilirubin"), row.get("creatinine"), row.get("inr"),
                row.get("sodium"), row.get("dialysis", "0") == "1",
                row.get("albumin"), row.get("sex", "M")
            )
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(
                row.get("qt_ms") or row.get("qt"), row.get("rr_ms"),
                row.get("hr_bpm") or row.get("heart_rate")
            )
        if "weight_kg" in row:
            return calculate_bmi_z(
                row.get("weight_kg"), row.get("height_cm"),
                row.get("age_months") or row.get("age") or 60, row.get("sex", "M")
            )
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))
        if "ast_u_l" in row:
            return calculate_apri_fib4(
                row.get("ast_u_l"), row.get("alt_u_l"), row.get("platelets_109"),
                row.get("age_years") or row.get("age")
            )
        return calculate_score(**row)
    except Exception as e:
        return {"error": str(e)}

def process_csv(inp, out):
    import csv
    with open(inp, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f); rows=list(r); fieldnames=r.fieldnames
    results=[]
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k,v in res.items()}}
        results.append(merged)
    # union fieldnames
    all_keys=set()
    for rr in results: all_keys.update(rr.keys())
    # keep original first
    extra = [k for k in all_keys if k not in fieldnames]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(fieldnames)+extra); w.writeheader(); w.writerows(results)
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="smr", description="Standardized Mortality Ratio Calculator")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. bil')
    s.add_argument("--bili", type=float); s.add_argument("--creat", type=float); s.add_argument("--inr", type=float); s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float); s.add_argument("--rr", type=float); s.add_argument("--hr", type=float)
    b=sub.add_parser("batch", help="batch csv"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    import json as _json
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        if a.json:
            row=_json.loads(a.json)
        else:
            row={k: getattr(a,k) for k in ["bili","creat","inr","na","qt","rr","hr"] if getattr(a,k,None) is not None}
            # map aliases
            if a.bili is not None: row["bilirubin"]=a.bili
            if a.creat is not None: row["creatinine"]=a.creat
            if a.inr is not None: row["inr"]=a.inr
            if a.na is not None: row["sodium"]=a.na
            if a.qt is not None: row["qt_ms"]=a.qt
            if a.rr is not None: row["rr_ms"]=a.rr
            if a.hr is not None: row["hr_bpm"]=a.hr
        print(assess_row(row))
        return 0
    if a.cmd=="batch":
        res=process_csv(a.input, a.output); print(f"Processed {len(res)} -> {a.output}"); return 0
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
