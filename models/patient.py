# models/patient.py
from pydantic import BaseModel
from typing import Optional

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
