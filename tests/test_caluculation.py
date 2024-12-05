# tests/test_calculation.py
import pytest
from models import Patient, Solution, InfusionMix
from calculation import calculate_infusion

def test_calculate_infusion():
    # テスト用のデータ設定
    patient = Patient(
        weight=1.33,
        twi=110,
        gir=7.0,
        amino_acid=3.0,
        na=2.5,
        k=1.5,
        p=1.5
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
    assert "総投与量 (TWI)" in infusion_mix.calculation_steps
    assert "必要GIR" in infusion_mix.calculation_steps
    assert "必要アミノ酸量" in infusion_mix.calculation_steps
    assert "必要Na量" in infusion_mix.calculation_steps
    assert "必要K量" in infusion_mix.calculation_steps
    assert "必要P量" in infusion_mix.calculation_steps
    assert "ブドウ糖濃度" in infusion_mix.calculation_steps
    assert "アミノ酸濃度" in infusion_mix.calculation_steps
    assert "ベース製剤からのNa量" in infusion_mix.calculation_steps
    assert "リン酸NaからのNa濃度" in infusion_mix.calculation_steps
    assert "ベース製剤からのK量" in infusion_mix.calculation_steps
    assert "KClからのK濃度" in infusion_mix.calculation_steps
    assert "リン酸NaからのP濃度" in infusion_mix.calculation_steps
    assert "計算された総液量" in infusion_mix.calculation_steps
    assert "必要水量" in infusion_mix.calculation_steps
    assert "蒸留水の量" in infusion_mix.calculation_steps
