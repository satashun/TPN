# models/additive.py

from pydantic import BaseModel
from typing import Optional

class Additive(BaseModel):
    name: str
    amino_acid_concentration: Optional[float] = 0.0  # g/mL
    amino_acid_concentration_unit: Optional[str] = "g/mL"
    zn_concentration: Optional[float] = 0.0          # mmol/mL
    zn_concentration_unit: Optional[str] = "mmol/mL"
    na_concentration: Optional[float] = 0.0          # mEq/mL
    na_concentration_unit: Optional[str] = "mEq/mL"
    p_concentration: Optional[float] = 0.0           # mmol/mL
    p_concentration_unit: Optional[str] = "mmol/mL"
    k_concentration: Optional[float] = 0.0           # mEq/mL
    k_concentration_unit: Optional[str] = "mEq/mL"
    cl_concentration: Optional[float] = 0.0          # mEq/mL
    cl_concentration_unit: Optional[str] = "mEq/mL"
    ca_concentration: Optional[float] = 0.0          # mEq/mL
    ca_concentration_unit: Optional[str] = "mEq/mL"
    mg_concentration: Optional[float] = 0.0          # mEq/mL
    mg_concentration_unit: Optional[str] = "mEq/mL"
    fat_concentration: Optional[float] = 0.0         # g/mL
    fat_concentration_unit: Optional[str] = "g/mL"
