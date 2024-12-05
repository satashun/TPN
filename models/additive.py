# models/additive.py
from pydantic import BaseModel
from typing import Optional

class Additive(BaseModel):
    name: str
    # リン酸Naの場合
    p_concentration: Optional[float] = None  # mmol/mL
    p_concentration_unit: Optional[str] = None
    na_concentration: Optional[float] = None  # mEq/mL or g/mL
    na_concentration_unit: Optional[str] = None
    # 脂肪の場合
    fat_concentration: Optional[float] = None  # g/mL
    fat_concentration_unit: Optional[str] = None
    # Caの場合
    ca_concentration: Optional[float] = None  # mEq/mL
    ca_concentration_unit: Optional[str] = None
