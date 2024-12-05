# models/infusion_mix.py
from pydantic import BaseModel
from typing import Optional, Dict

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
