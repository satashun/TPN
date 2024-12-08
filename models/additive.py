# models/additive.py

from pydantic import BaseModel

class Additive(BaseModel):
    name: str
    amino_acid_concentration: float
    amino_acid_concentration_unit: str
    zn_concentration: float
    zn_concentration_unit: str
    na_concentration: float
    na_concentration_unit: str
    p_concentration: float
    p_concentration_unit: str
    k_concentration: float
    k_concentration_unit: str
    cl_concentration: float
    cl_concentration_unit: str
    ca_concentration: float
    ca_concentration_unit: str
    mg_concentration: float
    mg_concentration_unit: str
    fat_concentration: float
    fat_concentration_unit: str
