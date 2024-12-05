# models/additive.py
from pydantic import BaseModel, Field
from typing import Optional

class Additive(BaseModel):
    name: str
    p_concentration: Optional[float] = Field(default=0.0, description="P濃度 (mmol/mL)")
    p_concentration_unit: Optional[str] = Field(default="mmol/mL")
    na_concentration: Optional[float] = Field(default=0.0, description="Na濃度 (mEq/mL)")
    na_concentration_unit: Optional[str] = Field(default="mEq/mL")
    ca_concentration: Optional[float] = Field(default=0.0, description="Ca濃度 (mEq/mL)")
    ca_concentration_unit: Optional[str] = Field(default="mEq/mL")
    amino_acid_concentration: Optional[float] = Field(default=0.0, description="アミノ酸濃度 (g/mL)")  # 追加
    amino_acid_concentration_unit: Optional[str] = Field(default="g/mL")  # 追加
    k_concentration: Optional[float] = Field(default=0.0, description="K濃度 (mEq/mL)")  # 追加
    k_concentration_unit: Optional[str] = Field(default="mEq/mL")  # 追加
    fat_concentration: Optional[float] = Field(default=0.0, description="脂肪濃度 (g/mL)")  # 追加
    fat_concentration_unit: Optional[str] = Field(default="g/mL")  # 追加
