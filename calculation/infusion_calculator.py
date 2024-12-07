# calculation/infusion_calculator.py

from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from typing import Dict
import logging

def get_safe_concentration(obj: object, attribute: str, default=0.0) -> float:
    """
    指定されたオブジェクトから濃度を安全に取得します。
    """
    concentration = getattr(obj, attribute, default)
    if concentration is None:
        logging.warning(f"{attribute} for {obj.name if hasattr(obj,'name') else obj} is None. Setting to {default}.")
        return default
    return concentration

def calc_requirement(value: float, included: bool, label: str, unit: str, weight: float) -> (float, str):
    """
    栄養素の必要量を計算し、計算ステップのログを生成します。
    """
    if included and value is not None:
        req = value * weight
        step = f"    - **{label}計算**\n        - {label}: {value} {unit} × {weight} kg = {req:.2f} {unit.replace('/kg/day','/day')}\n"
        return req, step
    else:
        step = f"    - **{label}計算**: 計算対象外\n"
        return 0.0, step

def required_volume(additional: float, concentration: float, additive_name: str) -> float:
    """
    添加剤の必要量を計算します。
    """
    if concentration > 0:
        return additional / concentration
    else:
        raise ValueError(f"{additive_name}の濃度が0です。")

def calculate_infusion(patient: Patient, base_solution: Solution, additives: Dict[str, Additive]) -> InfusionMix:
    """
    患者のデータとベース製剤、添加剤データを元にTPN配合を計算します。
    """
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択されたベース製剤: {base_solution}")
        logging.debug(f"選択された添加剤: {additives}")

        calculation_steps = "1. **投与量の計算**\n"
        nutrient_totals = {}
        detailed_mix = {}
        
        # GIR計算
        gir = patient.gir if patient.gir_included else None
        if gir:
            total_gir = gir * patient.weight * 1440 / 1000.0  # mg/kg/min -> g/day
            calculation_steps += f"    - **GIR計算**\n        - GIR: {gir} mg/kg/min × {patient.weight} kg × 1440 min/day / 1000 = {total_gir:.2f} g/day\n"
        else:
            total_gir = 0.0
            calculation_steps += "    - **GIR計算**: 計算対象外\n"

        # 各栄養素の目標値計算
        nutrients = {
            'Amino Acids': (patient.amino_acid, patient.amino_acid_included, "アミノ酸量", "g/kg/day"),
            'Na': (patient.na, patient.na_included, "Na量", "mEq/kg/day"),
            'K': (patient.k, patient.k_included, "K量", "mEq/kg/day"),
            'Cl': (patient.cl, patient.cl_included, "Cl量", "mEq/kg/day"),
            'Ca': (patient.ca, patient.ca_included, "Ca量", "mEq/kg/day"),
            'Mg': (patient.mg, patient.mg_included, "Mg量", "mEq/kg/day"),
            'Zn': (patient.zn, patient.zn_included, "Zn量", "mmol/kg/day"),
            'Fats': (patient.fat, patient.fat_included, "脂肪量", "g/kg/day")
        }

        for name, (value, included, label, unit) in nutrients.items():
            req, step = calc_requirement(value, included, label, unit, patient.weight)
            calculation_steps += step
            nutrient_totals[name] = req if included else 0.0

        # ベース製剤の栄養素供給量計算
        twi_volume = patient.twi * patient.weight  # mL/day
        detailed_mix[f"ベース製剤（{base_solution.name}）"] = twi_volume
        calculation_steps += f"2. **ベース製剤 ({base_solution.name}) 計算**\n        - ベース製剤量: {twi_volume:.2f} mL/day\n"

        base_supplies = {
            'Glucose': (base_solution.glucose_percentage / 100.0) * twi_volume,  # g/day
            'Na': base_solution.na * twi_volume / 1000.0,  # mEq/day
            'K': base_solution.k * twi_volume / 1000.0,  # mEq/day
            'Cl': base_solution.cl * twi_volume / 1000.0,  # mEq/day
            'P': base_solution.p * twi_volume / 1000.0,  # mmol/day
            'Calories': base_solution.calories * twi_volume / 1000.0,  # kcal/day
            'Mg': base_solution.mg * twi_volume / 1000.0,  # mEq/day
            'Ca': base_solution.ca * twi_volume / 1000.0,  # mEq/day
            'Zn': base_solution.zn * twi_volume / 1000.0  # mmol/day
        }

        for nutrient, supply in base_supplies.items():
            nutrient_totals[nutrient] = supply if nutrient not in nutrient_totals else nutrient_totals[nutrient] + supply

        # 必要な追加量計算と添加剤の追加
        calculation_steps += "3. **添加剤の計算**\n"

        # Na
        if nutrient_totals['Na'] < nutrient_totals.get('Na', 0.0):
            additional_na = nutrient_totals['Na'] - base_supplies['Na']
            if additional_na > 0:
                additive = additives.get("リン酸Na")
                if additive:
                    volume_na = required_volume(additional_na, get_safe_concentration(additive, 'na_concentration'), "リン酸Na")
                    detailed_mix["リン酸Na"] = volume_na
                    nutrient_totals['Na'] += additive.na_concentration * volume_na
                    nutrient_totals['P'] += additive.p_concentration * volume_na
                    calculation_steps += f"        - リン酸Naの追加量: {volume_na:.2f} mL/day\n"
                else:
                    raise ValueError("リン酸Naが添加剤に定義されていません。")

        # K
        if nutrient_totals['K'] < nutrient_totals.get('K', 0.0):
            additional_k = nutrient_totals['K'] - base_supplies['K']
            if additional_k > 0:
                additive = additives.get("KCl")
                if additive:
                    volume_k = required_volume(additional_k, get_safe_concentration(additive, 'k_concentration'), "KCl")
                    detailed_mix["KCl"] = volume_k
                    nutrient_totals['K'] += additive.k_concentration * volume_k
                    nutrient_totals['Cl'] += additive.cl_concentration * volume_k
                    calculation_steps += f"        - KClの追加量: {volume_k:.2f} mL/day\n"
                else:
                    raise ValueError("KClが添加剤に定義されていません。")

        # Ca
        if nutrient_totals['Ca'] < nutrient_totals.get('Ca', 0.0):
            additional_ca = nutrient_totals['Ca'] - base_supplies['Ca']
            if additional_ca > 0:
                additive = additives.get("カルチコール")
                if additive:
                    volume_ca = required_volume(additional_ca, get_safe_concentration(additive, 'ca_concentration'), "カルチコール")
                    detailed_mix["カルチコール"] = volume_ca
                    nutrient_totals['Ca'] += additive.ca_concentration * volume_ca
                    calculation_steps += f"        - カルチコールの追加量: {volume_ca:.2f} mL/day\n"
                else:
                    raise ValueError("カルチコールが添加剤に定義されていません。")

        # Mg
        if nutrient_totals['Mg'] < nutrient_totals.get('Mg', 0.0):
            additional_mg = nutrient_totals['Mg'] - base_supplies['Mg']
            if additional_mg > 0:
                additive = additives.get("リン酸Mg")  # リン酸Mgが存在することを前提とします
                if additive:
                    volume_mg = required_volume(additional_mg, get_safe_concentration(additive, 'mg_concentration'), "リン酸Mg")
                    detailed_mix["リン酸Mg"] = volume_mg
                    nutrient_totals['Mg'] += additive.mg_concentration * volume_mg
                    nutrient_totals['P'] += additive.p_concentration * volume_mg
                    calculation_steps += f"        - リン酸Mgの追加量: {volume_mg:.2f} mL/day\n"
                else:
                    raise ValueError("リン酸Mgが添加剤に定義されていません。")

        # Zn
        if nutrient_totals['Zn'] < nutrient_totals.get('Zn', 0.0):
            additional_zn = nutrient_totals['Zn'] - base_supplies['Zn']
            if additional_zn > 0:
                additive = additives.get("プレアミンP")
                if additive:
                    volume_zn = required_volume(additional_zn, get_safe_concentration(additive, 'zn_concentration'), "プレアミンP")
                    detailed_mix["プレアミンP"] = volume_zn
                    nutrient_totals['Zn'] += additive.zn_concentration * volume_zn
                    calculation_steps += f"        - プレアミンPの追加量: {volume_zn:.2f} mL/day\n"
                else:
                    raise ValueError("プレアミンPが添加剤に定義されていません。")

        # Amino Acids
        if nutrient_totals['Amino Acids'] < nutrient_totals.get('Amino Acids', 0.0):
            additional_aa = nutrient_totals['Amino Acids'] - nutrient_totals.get('Amino Acids', 0.0)
            if additional_aa > 0:
                additive = additives.get("プレアミンP")
                if additive and additive.amino_acid_concentration > 0:
                    volume_aa = required_volume(additional_aa, additive.amino_acid_concentration, "プレアミンP")
                    detailed_mix["プレアミンP"] += volume_aa if "プレアミンP" in detailed_mix else volume_aa
                    nutrient_totals['Amino Acids'] += additive.amino_acid_concentration * volume_aa
                    calculation_steps += f"        - プレアミンPの追加量: {volume_aa:.2f} mL/day\n"
                else:
                    raise ValueError("プレアミンPにアミノ酸濃度が定義されていません。")

        # Fats
        if nutrient_totals['Fats'] < nutrient_totals.get('Fats', 0.0):
            additional_fat = nutrient_totals['Fats'] - nutrient_totals.get('Fats', 0.0)
            if additional_fat > 0:
                additive = additives.get("イントラリポス20%")
                if additive and additive.fat_concentration > 0:
                    volume_fat = required_volume(additional_fat, additive.fat_concentration, "イントラリポス20%")
                    detailed_mix["イントラリポス20%"] = volume_fat
                    nutrient_totals['Fats'] += additive.fat_concentration * volume_fat
                    calculation_steps += f"        - イントラリポス20%の追加量: {volume_fat:.2f} mL/day\n"
                else:
                    raise ValueError("イントラリポス20%に脂肪濃度が定義されていません。")

        # GIR用ブドウ糖液の追加
        if total_gir > 0:
            glucose_conc = 0.5  # 50%ブドウ糖液: 0.5 g/mL
            glu_vol = total_gir / glucose_conc  # g/day / (g/mL) = mL/day
            detailed_mix["50%ブドウ糖液"] = glu_vol
            nutrient_totals['Glucose'] += glucose_conc * glu_vol
            calculation_steps += f"        - 50%ブドウ糖液の追加量: {glu_vol:.2f} mL/day\n"

        # 蒸留水の追加
        calculated_total_volume = sum(detailed_mix.values())
        water_volume = twi_volume - calculated_total_volume
        if water_volume > 0:
            detailed_mix["蒸留水"] = water_volume
            calculation_steps += f"        - 蒸留水の追加量: {water_volume:.2f} mL/day\n"

        # nutrient_units の定義
        nutrient_units = {
            'Na': 'mEq/day',
            'K': 'mEq/day',
            'Cl': 'mEq/day',
            'Ca': 'mEq/day',
            'Mg': 'mEq/day',
            'Zn': 'mmol/day',
            'P': 'mmol/day',
            'Amino Acids': 'g/day',
            'Fats': 'g/day',
            'Glucose': 'g/day'
        }

        # input_amounts と input_units の定義
        input_amounts = {}
        input_units = {}
        if patient.gir_included and patient.gir is not None:
            input_amounts['GIR'] = patient.gir
            input_units['GIR'] = "mg/kg/min"
        if patient.amino_acid_included and patient.amino_acid is not None:
            input_amounts['Amino Acids'] = patient.amino_acid
            input_units['Amino Acids'] = "g/kg/day"
        if patient.na_included and patient.na is not None:
            input_amounts['Na'] = patient.na
            input_units['Na'] = "mEq/kg/day"
        if patient.k_included and patient.k is not None:
            input_amounts['K'] = patient.k
            input_units['K'] = "mEq/kg/day"
        if patient.cl_included and patient.cl is not None:
            input_amounts['Cl'] = patient.cl
            input_units['Cl'] = "mEq/kg/day"
        if patient.ca_included and patient.ca is not None:
            input_amounts['Ca'] = patient.ca
            input_units['Ca'] = "mEq/kg/day"
        if patient.mg_included and patient.mg is not None:
            input_amounts['Mg'] = patient.mg
            input_units['Mg'] = "mEq/kg/day"
        if patient.zn_included and patient.zn is not None:
            input_amounts['Zn'] = patient.zn
            input_units['Zn'] = "mmol/kg/day"
        if patient.fat_included and patient.fat is not None:
            input_amounts['Fats'] = patient.fat
            input_units['Fats'] = "g/kg/day"

        infusion_mix = InfusionMix(
            gir=patient.gir if patient.gir_included else None,
            amino_acid=patient.amino_acid if patient.amino_acid_included else None,
            na=patient.na if patient.na_included else None,
            k=patient.k if patient.k_included else None,
            p=patient.p if patient.p_included else None,
            fat=patient.fat if patient.fat_included else None,
            ca=patient.ca if patient.ca_included else None,
            mg=patient.mg if patient.mg_included else None,
            zn=patient.zn if patient.zn_included else None,
            cl=patient.cl if patient.cl_included else None,
            detailed_mix=detailed_mix,
            calculation_steps=calculation_steps,
            nutrient_totals=nutrient_totals,
            nutrient_units=nutrient_units,
            input_amounts=input_amounts,
            input_units=input_units
        )

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
