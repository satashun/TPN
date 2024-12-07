# models/infusion_mix.py

from pydantic import BaseModel
from typing import Dict, Optional

class InfusionMix(BaseModel):
    gir: Optional[float]  # mg/kg/min
    amino_acid: Optional[float]  # g/kg/day
    na: Optional[float]  # mEq/kg/day
    k: Optional[float]  # mEq/kg/day
    p: Optional[float]  # mmol/kg/day
    fat: Optional[float]  # g/kg/day
    ca: Optional[float]  # mEq/kg/day
    mg: Optional[float]  # mEq/kg/day
    zn: Optional[float]  # mmol/kg/day
    cl: Optional[float]  # mEq/kg/day
    detailed_mix: Dict[str, float]  # 製剤名: mL/day
    calculation_steps: str
    nutrient_totals: Dict[str, float]  # 各栄養素の総量
    nutrient_units: Dict[str, str]  # 各栄養素の単位
    input_amounts: Dict[str, float]
    input_units: Dict[str, str]
