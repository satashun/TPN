# models.py
from pydantic import BaseModel
from typing import Optional, Dict

class Solution(BaseModel):
    name: str
    glucose_percentage: float  # ブドウ糖濃度 (%)
    glucose_unit: str
    na: float  # Na⁺ (mEq/L)
    na_unit: str
    k: float  # K⁺ (mEq/L)
    k_unit: str
    cl: float  # Cl⁻ (mEq/L)
    cl_unit: str
    p: float  # P (mmol/L)
    p_unit: str
    calories: float  # カロリー (kcal/L)
    calories_unit: str

class Additive(BaseModel):
    name: str
    # リン酸Naの場合
    p_concentration: Optional[float] = None  # mmol/mL
    p_concentration_unit: Optional[str] = None
    na_concentration: Optional[float] = None  # mEq/mL or g/mL
    na_concentration_unit: Optional[str] = None
    # 脂肪の場合
    fat_concentration: Optional[float] = None  # g/mL
    fat_concentration_unit: Optional[str] = None
    # Caの場合
    ca_concentration: Optional[float] = None  # mEq/mL
    ca_concentration_unit: Optional[str] = None

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
    fat: Optional[float] = None  # g/kg/day
    fat_included: bool = False
    ca: Optional[float] = None  # mEq/kg/day
    ca_included: bool = False

class InfusionMix(BaseModel):
    gir: Optional[float]  # mg/kg/min
    amino_acid: Optional[float]  # g/kg/day
    na: Optional[float]  # mEq/kg/day
    k: Optional[float]  # mEq/kg/day
    p: Optional[float]  # mmol/kg/day
    fat: Optional[float]  # g/kg/day
    ca: Optional[float]  # mEq/kg/day
    detailed_mix: Optional[Dict[str, float]] = None  # 混合溶液の詳細
    calculation_steps: Optional[str] = None  # 計算ステップの詳細
