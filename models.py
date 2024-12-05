# models.py
from pydantic import BaseModel
from typing import Optional, Dict

class Solution(BaseModel):
    name: str
    glucose_percentage: float  # ブドウ糖濃度 (%)
    na: float  # Na⁺ (mEq/L)
    k: float  # K⁺ (mEq/L)
    cl: float  # Cl⁻ (mEq/L)
    p: float  # P (mmol/L)
    calories: float  # カロリー (kcal/L)

class Patient(BaseModel):
    weight: float  # kg
    twi: float  # mL/kg/day
    gir: Optional[float] = None  # mg/kg/min
    gir_included: bool = True
    amino_acid: Optional[float] = None  # g/kg/day
    amino_acid_included: bool = True
    na: Optional[float] = None  # mEq/kg/day
    na_included: bool = True
    k: Optional[float] = None  # mEq/kg/day
    k_included: bool = True
    p: Optional[float] = None  # mmol/kg/day
    p_included: bool = True

class InfusionMix(BaseModel):
    gir: Optional[float]  # mg/kg/min
    amino_acid: Optional[float]  # g/kg/day
    na: Optional[float]  # mEq/kg/day
    k: Optional[float]  # mEq/kg/day
    p: Optional[float]  # mmol/kg/day
    detailed_mix: Optional[Dict[str, float]] = None  # 混合溶液の詳細
    calculation_steps: Optional[str] = None  # 計算ステップの詳細
