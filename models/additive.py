# models/additive.py
from pydantic import BaseModel, Field, validator
from typing import Optional

class Additive(BaseModel):
    name: str
    p_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="P濃度 (mmol/mL)")
    p_concentration_unit: Optional[str] = Field(default="mmol/mL")
    na_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="Na濃度 (mEq/mL)")
    na_concentration_unit: Optional[str] = Field(default="mEq/mL")
    ca_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="Ca濃度 (mEq/mL)")
    ca_concentration_unit: Optional[str] = Field(default="mEq/mL")
    amino_acid_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="アミノ酸濃度 (g/mL)")
    amino_acid_concentration_unit: Optional[str] = Field(default="g/mL")
    k_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="K濃度 (mEq/mL)")
    k_concentration_unit: Optional[str] = Field(default="mEq/mL")
    fat_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="脂肪濃度 (g/mL)")
    fat_concentration_unit: Optional[str] = Field(default="g/mL")
    cl_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="Cl濃度 (mEq/mL)")
    cl_concentration_unit: Optional[str] = Field(default="mEq/mL")
    zn_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="Zn濃度 (mmol/mL)")
    zn_concentration_unit: Optional[str] = Field(default="mmol/mL")
    mg_concentration: Optional[float] = Field(default=0.0, ge=0.0, description="Mg濃度 (mEq/mL)")
    mg_concentration_unit: Optional[str] = Field(default="mEq/mL")

    @validator('*', pre=True, always=True)
    def set_default(cls, v):
        return v or 0.0
