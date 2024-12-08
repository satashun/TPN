# models/patient.py

from pydantic import BaseModel
from typing import Optional

class Patient(BaseModel):
    weight: float  # kg
    twi: float  # mL/kg/day
    gir: Optional[float] = None  # mg/kg/min
    gir_included: bool = False
    amino_acid: Optional[float] = None  # g/kg/day
    amino_acid_included: bool = False
    na: Optional[float] = None  # mEq/kg/day
    na_included: bool = False
    k: Optional[float] = None  # mEq/kg/day
    k_included: bool = False
    p: Optional[float] = None  # mmol/kg/day
    p_included: bool = False
    fat: Optional[float] = None  # g/kg/day
    fat_included: bool = False
    ca: Optional[float] = None  # mEq/kg/day
    ca_included: bool = False
    mg: Optional[float] = None  # mEq/kg/day
    mg_included: bool = False
    zn: Optional[float] = None  # mmol/kg/day
    zn_included: bool = False
    cl: Optional[float] = None  # mEq/kg/day
    cl_included: bool = False
