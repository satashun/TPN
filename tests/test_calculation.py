# tests/test_calculation.py
import pytest
from models import Patient, Solution, Additive, InfusionMix
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
        p_included=True,
        fat=2.0,
        fat_included=True,
        ca=1.0,
        ca_included=True
    )
    
    base_solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    additives = {
        "リン酸Na": Additive(
            name="リン酸Na",
            p_concentration=10.0,
            na_concentration=15.0
        ),
        "イントラリポス": Additive(
            name="イントラリポス",
            fat_concentration=20.0
        ),
        "カルチコール": Additive(
            name="カルチコール",
            ca_concentration=10.0
        ),
        "プレアミンP": Additive(
            name="プレアミンP",
            na_concentration=0.076  # g/mL
        ),
        "KCl": Additive(
            name="KCl",
            na_concentration=1.0  # mEq/mL
        )
    }
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, base_solution, additives)
    
    # 結果の検証
    assert infusion_mix.gir == 7.0
    assert infusion_mix.amino_acid == 3.0
    assert infusion_mix.na == 2.5
    assert infusion_mix.k == 1.5
    assert infusion_mix.p == 1.5
    assert infusion_mix.fat == 2.0
    assert infusion_mix.ca == 1.0
    
    # 詳細な配合量の検証
    assert "ソルデム3AG" in infusion_mix.detailed_mix
    assert "プレアミンP" in infusion_mix.detailed_mix
    assert "リン酸Na" in infusion_mix.detailed_mix
    assert "KCl" in infusion_mix.detailed_mix
    assert "イントラリポス" in infusion_mix.detailed_mix
    assert "カルチコール" in infusion_mix.detailed_mix
    assert "蒸留水" in infusion_mix.detailed_mix

    # 計算ステップの検証
    assert infusion_mix.calculation_steps is not None
    steps = infusion_mix.calculation_steps
    assert "1. **総投与量 (TWI)**" in steps
    assert "2. **必要量**" in steps
    assert "    - **GIR**" in steps
    assert "    - **アミノ酸量**" in steps
    assert "    - **Na量**" in steps
    assert "    - **K量**" in steps
    assert "    - **P量**" in steps
    assert "    - **脂肪**" in steps
    assert "    - **Ca量**" in steps
    assert "3. **投与計算**" in steps
    assert "    - **ブドウ糖計算**" in steps
    assert "    - **アミノ酸計算**" in steps
    assert "    - **Na量計算**" in steps
    assert "    - **リン酸NaからのNa計算**" in steps
    assert "    - **K量計算**" in steps
    assert "    - **KClからのK計算**" in steps
    assert "    - **リン酸NaからのP計算**" in steps
    assert "    - **脂肪計算**" in steps
    assert "    - **Ca量計算**" in steps
    assert "4. **総液量計算**" in steps
    assert "    - 総液量: " in steps
    assert "    - 必要水量: " in steps
    assert "5. **蒸留水の量**" in steps
    assert "6. **配合量の詳細**" in steps
    assert "    - ソルデム3AG:" in steps
    assert "    - プレアミンP:" in steps
    assert "    - リン酸Na:" in steps
    assert "    - KCl:" in steps
    assert "    - イントラリポス:" in steps
    assert "    - カルチコール:" in steps
    assert "    - 蒸留水:" in steps

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
        p_included=True,
        fat=2.0,
        fat_included=True,
        ca=1.0,
        ca_included=True
    )
    
    base_solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    additives = {
        "リン酸Na": Additive(
            name="リン酸Na",
            p_concentration=10.0,
            na_concentration=15.0
        ),
        "イントラリポス": Additive(
            name="イントラリポス",
            fat_concentration=20.0
        ),
        "カルチコール": Additive(
            name="カルチコール",
            ca_concentration=10.0
        ),
        "プレアミンP": Additive(
            name="プレアミンP",
            na_concentration=0.076  # g/mL
        ),
        "KCl": Additive(
            name="KCl",
            na_concentration=1.0  # mEq/mL
        )
    }
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, base_solution, additives)
    
    # GIRがNoneであることの検証
    assert infusion_mix.gir is None

    # 計算ステップにGIRのステップが計算対象外として含まれていることを検証
    steps = infusion_mix.calculation_steps
    assert "2. **必要量**" in steps
    assert "    - **GIR**: 計算対象外" in steps

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
        p_included=False,
        fat=None,
        fat_included=False,
        ca=None,
        ca_included=False
    )
    
    base_solution = Solution(
        name="ソルデム3AG",
        glucose_percentage=75.0,  # %
        na=35,
        k=20,
        cl=35,
        p=0,
        calories=300
    )
    
    additives = {
        "リン酸Na": Additive(
            name="リン酸Na",
            p_concentration=10.0,
            na_concentration=15.0
        ),
        "イントラリポス": Additive(
            name="イントラリポス",
            fat_concentration=20.0
        ),
        "カルチコール": Additive(
            name="カルチコール",
            ca_concentration=10.0
        ),
        "プレアミンP": Additive(
            name="プレアミンP",
            na_concentration=0.076  # g/mL
        ),
        "KCl": Additive(
            name="KCl",
            na_concentration=1.0  # mEq/mL
        )
    }
    
    # 計算実行
    infusion_mix = calculate_infusion(patient, base_solution, additives)
    
    # 全てのオプション栄養素がNoneであることの検証
    assert infusion_mix.gir is None
    assert infusion_mix.amino_acid is None
    assert infusion_mix.na is None
    assert infusion_mix.k is None
    assert infusion_mix.p is None
    assert infusion_mix.fat is None
    assert infusion_mix.ca is None

    # 計算ステップにオプション栄養素のステップが計算対象外として含まれていることを検証
    steps = infusion_mix.calculation_steps
    assert "2. **必要量**" in steps
    assert "    - **GIR**: 計算対象外" in steps
    assert "    - **アミノ酸量**: 計算対象外" in steps
    assert "    - **Na量**: 計算対象外" in steps
    assert "    - **K量**: 計算対象外" in steps
    assert "    - **P量**: 計算対象外" in steps
    assert "    - **脂肪**: 計算対象外" in steps
    assert "    - **Ca量**: 計算対象外" in steps
