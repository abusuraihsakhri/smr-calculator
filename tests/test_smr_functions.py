"""
Automated Pytest Test Suite for smr-calculator clinical calculation functions.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import smr


class TestCalculateMELDNa:
    """Tests for MELD-Na liver disease severity score."""

    def test_basic_meld_na_calculation(self):
        result = smr.calculate_meld_na(
            bilirubin=2.0, creatinine=1.5, inr=1.2, sodium=135
        )
        assert "score" in result
        assert "meld_base" in result
        assert "meld_na" in result
        assert 6 <= result["score"] <= 40

    def test_meld_na_with_dialysis(self):
        result = smr.calculate_meld_na(
            bilirubin=3.0, creatinine=1.0, inr=1.5, sodium=130, dialysis=True
        )
        # Dialysis should cap creatinine at 4.0, increasing score
        assert result["score"] >= 6

    def test_meld_na_high_values(self):
        result = smr.calculate_meld_na(
            bilirubin=20.0, creatinine=3.5, inr=3.0, sodium=125
        )
        assert result["interpretation"] == "high"
        assert result["score"] <= 40

    def test_meld_na_low_values(self):
        result = smr.calculate_meld_na(
            bilirubin=0.5, creatinine=0.5, inr=0.8, sodium=140
        )
        assert result["interpretation"] == "low"

    def test_meld_na_none_values(self):
        result = smr.calculate_meld_na(
            bilirubin=None, creatinine=None, inr=None, sodium=None
        )
        assert "score" in result


class TestCalculateQTc:
    """Tests for QTc interval correction."""

    def test_qtc_with_heart_rate(self):
        result = smr.calculate_qtc(qt_ms=400, hr_bpm=70)
        assert "qtc_ms" in result
        assert result["qt_ms"] == 400.0
        assert result["interpretation"] in ["normal", "borderline", "prolonged"]

    def test_qtc_with_rr_interval(self):
        result = smr.calculate_qtc(qt_ms=400, rr_ms=800)
        assert "qtc_ms" in result
        assert result["rr_ms"] == 800.0

    def test_qtc_prolonged(self):
        result = smr.calculate_qtc(qt_ms=550, hr_bpm=60)
        assert result["interpretation"] == "prolonged"

    def test_qtc_normal(self):
        result = smr.calculate_qtc(qt_ms=380, hr_bpm=75)
        assert result["interpretation"] == "normal"

    def test_qtc_invalid_qt(self):
        result = smr.calculate_qtc(qt_ms=0, hr_bpm=70)
        assert "error" in result

    def test_qtc_no_rr_or_hr(self):
        result = smr.calculate_qtc(qt_ms=400)
        assert "error" in result


class TestCalculateBMIZ:
    """Tests for BMI Z-score calculation."""

    def test_basic_bmi_z(self):
        result = smr.calculate_bmi_z(weight_kg=70, height_cm=175, age_months=60, sex="M")
        assert "bmi" in result
        assert "z_score" in result
        assert "interpretation" in result

    def test_bmi_z_invalid_input(self):
        result = smr.calculate_bmi_z(weight_kg=0, height_cm=175)
        assert "error" in result

    def test_bmi_z_negative_height(self):
        result = smr.calculate_bmi_z(weight_kg=70, height_cm=-175)
        assert "error" in result

    def test_bmi_z_infant(self):
        result = smr.calculate_bmi_z(weight_kg=10, height_cm=75, age_months=12)
        assert "bmi" in result


class TestConvertHbA1c:
    """Tests for HbA1c to eAG conversion."""

    def test_hba1c_to_eag(self):
        result = smr.convert_hba1c(hba1c_percent=6.0)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result
        assert "eag_mmol_l" in result
        assert result["interpretation"] == "prediabetic"

    def test_eag_to_hba1c(self):
        result = smr.convert_hba1c(eag_mgdl=125.5)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result

    def test_hba1c_diabetic(self):
        result = smr.convert_hba1c(hba1c_percent=7.0)
        assert result["interpretation"] == "diabetic"

    def test_hba1c_normal(self):
        result = smr.convert_hba1c(hba1c_percent=5.0)
        assert result["interpretation"] == "normal"

    def test_hba1c_no_input(self):
        result = smr.convert_hba1c()
        assert "error" in result


class TestCalculateAPRIFIB4:
    """Tests for APRI and FIB-4 liver fibrosis scores."""

    def test_apri_only(self):
        result = smr.calculate_apri_fib4(ast_u_l=80, platelets_109=200)
        assert "apri" in result
        assert "ast_ratio" in result

    def test_apri_and_fib4(self):
        result = smr.calculate_apri_fib4(
            ast_u_l=80, alt_u_l=60, platelets_109=200, age_years=50
        )
        assert "apri" in result
        assert "fib4" in result
        assert result["fib4_interpretation"] in ["advanced_fibrosis", "indeterminate", "low_risk"]

    def test_apri_invalid_ast(self):
        result = smr.calculate_apri_fib4(ast_u_l=0)
        assert "error" in result

    def test_apri_no_platelets(self):
        result = smr.calculate_apri_fib4(ast_u_l=80)
        assert "ast_ratio" in result
        assert "apri" not in result


class TestAssessRow:
    """Tests for the assess_row dispatcher function."""

    def test_assess_row_meld_na(self):
        result = smr.assess_row({
            "bilirubin": 2.0, "creatinine": 1.5, "inr": 1.2, "sodium": 135
        })
        assert "score" in result
        assert "meld_na" in result

    def test_assess_row_qtc(self):
        result = smr.assess_row({"qt_ms": 400, "hr_bpm": 70})
        assert "qtc_ms" in result

    def test_assess_row_bmi(self):
        result = smr.assess_row({
            "weight_kg": 70, "height_cm": 175, "age_months": 60, "sex": "M"
        })
        assert "bmi" in result

    def test_assess_row_hba1c(self):
        result = smr.assess_row({"hba1c_percent": 6.0})
        assert "eag_mgdl" in result

    def test_assess_row_apri(self):
        result = smr.assess_row({
            "ast_u_l": 80, "alt_u_l": 60, "platelets_109": 200, "age_years": 50
        })
        assert "apri" in result

    def test_assess_row_generic_score(self):
        result = smr.assess_row({"value": 10})
        assert "score" in result
        assert "inputs" in result


class TestSafeFloat:
    """Tests for the _safe_float helper function."""

    def test_none_value(self):
        assert smr._safe_float(None) == 0.0

    def test_valid_float(self):
        assert smr._safe_float("3.14") == 3.14

    def test_invalid_string(self):
        assert smr._safe_float("not a number") == 0.0

    def test_custom_default(self):
        assert smr._safe_float(None, default=1.0) == 1.0

    def test_integer_input(self):
        assert smr._safe_float(42) == 42.0
