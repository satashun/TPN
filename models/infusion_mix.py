# models/infusion_mix.py

from pydantic import BaseModel
from typing import Optional, Dict

class InfusionMix(BaseModel):
    gir: Optional[float] = None
    amino_acid: Optional[float] = None
    na: Optional[float] = None
    k: Optional[float] = None
    p: Optional[float] = None
    fat: Optional[float] = None
    ca: Optional[float] = None
    mg: Optional[float] = None
    zn: Optional[float] = None
    cl: Optional[float] = None
    detailed_mix: Dict[str, float]
    calculation_steps: str
    nutrient_totals: Dict[str, float]
    nutrient_units: Dict[str, str]
    input_amounts: Dict[str, float]
    input_units: Dict[str, str]
