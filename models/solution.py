# models/solution.py

from pydantic import BaseModel

class Solution(BaseModel):
    name: str
    glucose_percentage: float  # ブドウ糖濃度 (%または g/L)
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
    mg: float  # Mg²⁺ (mEq/L)
    mg_unit: str
    ca: float  # Ca²⁺ (mEq/L)
    ca_unit: str
    zn: float  # Zn (mmol/L)
    zn_unit: str
    fat_concentration: float  # 脂肪濃度 (g/mL)
    fat_concentration_unit: str  # 脂肪濃度の単位 (例: "g/mL")
