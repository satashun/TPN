# models/infusion_mix.py
from pydantic import BaseModel
from typing import Optional, Dict

class InfusionMix(BaseModel):
    gir: Optional[float]
    amino_acid: Optional[float]
    na: Optional[float]
    k: Optional[float]
    p: Optional[float]
    fat: Optional[float]
    ca: Optional[float]
    detailed_mix: Dict[str, float]
    calculation_steps: str
    nutrient_totals: Optional[Dict[str, float]] = {}  # 追加
    nutrient_units: Optional[Dict[str, str]] = {}    # 追加
