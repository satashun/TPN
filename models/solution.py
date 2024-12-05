# models/solution.py
from pydantic import BaseModel

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
