# tests/test_calculation.py
import pytest
from models import Patient, Solution, InfusionMix
from calculation import calculate_infusion

def test_calculate_infusion_with_all_parameters():
    # テスト用のデータ設定
    patient = Patient(
        weight=1.33,
        twi=110,
        gir=7.0,
        gir_included=True,
        amino_acid=3.0,
        amino_acid_included=True,
        na=2.5,
        na_included=True,
        k=1.5,
        k_included=True,
        p=1.5,
        p_included=True
    )
    
    solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, solution)
    
    # 結果の検証
    assert infusion_mix.gir == 7.0
    assert infusion_mix.amino_acid == 3.0
    assert infusion_mix.na == 2.5
    assert infusion_mix.k == 1.5
    assert infusion_mix.p == 1.5
    
    # 詳細な配合量の検証
    assert "ソルデム3AG" in infusion_mix.detailed_mix
    assert "プレアミンP" in infusion_mix.detailed_mix
    assert "リン酸Na" in infusion_mix.detailed_mix
    assert "KCl" in infusion_mix.detailed_mix
    assert "蒸留水" in infusion_mix.detailed_mix

    # 計算ステップの検証
    assert infusion_mix.calculation_steps is not None
    steps = infusion_mix.calculation_steps
    assert "1. **総投与量 (TWI)**" in steps
    assert "2. **必要GIR**" in steps
    assert "3. **必要アミノ酸量**" in steps
    assert "4. **必要Na量**" in steps
    assert "5. **必要K量**" in steps
    assert "6. **必要P量**" in steps
    assert "7. **ブドウ糖濃度**" in steps
    assert "8. **アミノ酸濃度**" in steps
    assert "9. **ベース製剤からのNa量**" in steps
    assert "10. **リン酸NaからのNa濃度**" in steps
    assert "11. **ベース製剤からのK量**" in steps
    assert "12. **KClからのK濃度**" in steps
    assert "13. **リン酸NaからのP濃度**" in steps
    assert "14. **計算された総液量**" in steps
    assert "15. **警告**" in steps
    assert "16. **蒸留水の量**" in steps
    assert "17. **配合量の詳細**" in steps

def test_calculate_infusion_without_gir():
    # GIRを含めない場合のテスト
    patient = Patient(
        weight=1.33,
        twi=110,
        gir=None,
        gir_included=False,
        amino_acid=3.0,
        amino_acid_included=True,
        na=2.5,
        na_included=True,
        k=1.5,
        k_included=True,
        p=1.5,
        p_included=True
    )
    
    solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, solution)
    
    # GIRがNoneであることの検証
    assert infusion_mix.gir is None

    # 計算ステップにGIRのステップが含まれていないことを検証
    assert "2. **必要GIR**" not in infusion_mix.calculation_steps

def test_calculate_infusion_without_any_optional_parameters():
    # 全てのオプション栄養素を含めない場合のテスト
    patient = Patient(
        weight=1.33,
        twi=110,
        gir=None,
        gir_included=False,
        amino_acid=None,
        amino_acid_included=False,
        na=None,
        na_included=False,
        k=None,
        k_included=False,
        p=None,
        p_included=False
    )
    
    solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, solution)
    
    # 全てのオプション栄養素がNoneであることの検証
    assert infusion_mix.gir is None
    assert infusion_mix.amino_acid is None
    assert infusion_mix.na is None
    assert infusion_mix.k is None
    assert infusion_mix.p is None

    # 計算ステップにオプション栄養素のステップが含まれていないことを検証
    steps = infusion_mix.calculation_steps
    assert "2. **必要GIR**" not in steps
    assert "3. **必要アミノ酸量**" not in steps
    assert "4. **必要Na量**" not in steps
    assert "5. **必要K量**" not in steps
    assert "6. **必要P量**" not in steps
