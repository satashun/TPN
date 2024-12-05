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
    gir: float  # mg/kg/min
    amino_acid: float  # g/kg/day
    na: float  # mEq/kg/day
    k: float  # mEq/kg/day
    p: float  # mmol/kg/day

class InfusionMix(BaseModel):
    gir: float  # mg/kg/min
    amino_acid: float  # g/kg/day
    na: float  # mEq/kg/day
    k: float  # mEq/kg/day
    p: float  # mmol/kg/day
    detailed_mix: Optional[Dict[str, float]] = None  # 混合溶液の詳細
    calculation_steps: Optional[str] = None  # 計算ステップの詳細
