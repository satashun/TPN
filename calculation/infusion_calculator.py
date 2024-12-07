# calculation/infusion_calculator.py

from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from typing import Dict
import logging

def get_safe_concentration(obj: object, attribute: str, default=0.0):
    concentration = getattr(obj, attribute, default)
    if concentration is None:
        logging.warning(f"{attribute} for {obj.name if hasattr(obj,'name') else obj} is None. Setting to {default}.")
        return default
    return concentration

def calculate_infusion(patient: Patient, base_solution: Solution, additives: Dict[str, Additive]) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択されたベース製剤: {base_solution}")
        logging.debug(f"選択された添加剤: {additives}")

        calculation_steps = "1. **投与量の計算**\n"
        step = 2
        input_amounts = {}
        input_units = {}

        calculation_steps_list = []

        # 必要量計算関数
        def calc_requirement(value, included, label, unit):
            if included and value is not None:
                req = value * patient.weight
                calculation_steps_list.append(f"    - **{label}計算**\n        - {label}: {value} {unit} × {patient.weight} kg = {req:.2f}{unit.replace('/kg/day','/day')}\n")
                input_amounts[label] = value
                input_units[label] = unit
                return req
            else:
                calculation_steps_list.append(f"    - **{label}計算**: 計算対象外\n")
                return 0.0

        # GIR計算
        if patient.gir_included and patient.gir is not None:
            total_gir = patient.gir * patient.weight * 1440 / 1000.0  # mg/kg/min * kg * min/day / 1000 = g/day
            calculation_steps_list.append(f"    - **GIR計算**\n        - GIR: {patient.gir} mg/kg/min × {patient.weight} kg × 1440 min/day / 1000 = {total_gir:.2f} g/day\n")
            input_amounts['GIR'] = patient.gir
            input_units['GIR'] = "mg/kg/min"
        else:
            total_gir = 0.0
            calculation_steps_list.append("    - **GIR計算**: 計算対象外\n")

        # 個々の要求量計算
        total_amino_acid = calc_requirement(patient.amino_acid, patient.amino_acid_included, "アミノ酸量", "g/kg/day")
        total_na = calc_requirement(patient.na, patient.na_included, "Na量", "mEq/kg/day")
        total_k = calc_requirement(patient.k, patient.k_included, "K量", "mEq/kg/day")
        total_cl = calc_requirement(patient.cl, patient.cl_included, "Cl量", "mEq/kg/day")
        total_ca = calc_requirement(patient.ca, patient.ca_included, "Ca量", "mEq/kg/day")
        total_mg = calc_requirement(patient.mg, patient.mg_included, "Mg量", "mEq/kg/day")
        total_zn = calc_requirement(patient.zn, patient.zn_included, "Zn量", "mmol/kg/day")
        total_fat = calc_requirement(patient.fat, patient.fat_included, "脂肪量", "g/kg/day")

        calculation_steps += "".join(calculation_steps_list) + "\n"
        calculation_steps += f"{step}. **投与計算**\n"
        step += 1

        # ベース製剤量
        twi_volume = patient.twi * patient.weight
        base_solution_volume = twi_volume
        calculation_steps += f"    - **ベース製剤 ({base_solution.name}) 計算**\n        - ベース製剤量: {base_solution_volume:.2f} mL/day\n"

        # ベース製剤からの供給量
        base_glucose = (base_solution.glucose_percentage / 100.0) * base_solution_volume  # g/day
        base_na = base_solution.na * base_solution_volume / 1000.0  # mEq/day
        base_k = base_solution.k * base_solution_volume / 1000.0  # mEq/day
        base_cl = base_solution.cl * base_solution_volume / 1000.0  # mEq/day
        base_p = base_solution.p * base_solution_volume / 1000.0  # mmol/day
        base_calories = base_solution.calories * base_solution_volume / 1000.0  # kcal/day
        base_mg = base_solution.mg * base_solution_volume / 1000.0  # mEq/day
        base_ca = base_solution.ca * base_solution_volume / 1000.0  # mEq/day
        base_zn = base_solution.zn * base_solution_volume / 1000.0  # mmol/day
        base_fat = 0.0  # ベース製剤に脂肪は含まれていないと仮定

        # 初期 nutrient_totals にベース製剤の栄養素を加算
        nutrient_totals = {
            'GIR': total_gir,  # GIRをグルコースとして扱う場合
            'Amino Acids': 0.0,
            'Na': base_na,
            'K': base_k,
            'Cl': base_cl,
            'Ca': base_ca,
            'Mg': base_mg,
            'Zn': base_zn,
            'P': base_p,
            'Fats': base_fat,
            'Glucose': base_glucose
        }

        # detailed_mix にベース製剤を追加
        detailed_mix = {f"ベース製剤（{base_solution.name}）": base_solution_volume}

        # 追加栄養素がベース製剤から供給されている場合は nutrient_totals に加算
        # ここでは既にベース製剤からの栄養素を nutrient_totals に追加済み

        # 各成分の差分計算
        calculation_steps += "    - **各成分の差分計算**\n"

        # 差分計算関数
        def required_volume_for_additive(total_req, base_sup, additive_name, conc_attr, unit=""):
            if total_req > base_sup:
                diff = total_req - base_sup
                add = additives.get(additive_name)
                if not add:
                    raise ValueError(f"'{additive_name}' が添加剤に定義されていません。")
                conc = get_safe_concentration(add, conc_attr, 0.0)
                if conc == 0:
                    raise ValueError(f"{additive_name}の{conc_attr}が0です。")
                vol = diff / conc
                return vol
            return 0.0

        # 各栄養素に対して必要な添加剤の量を計算
        # Na
        if total_na > base_na:
            vol_na = required_volume_for_additive(total_na, base_na, "リン酸Na", "na_concentration")
            if vol_na > 0:
                detailed_mix["リン酸Na"] = vol_na
                nutrient_totals['Na'] += add.na_concentration * vol_na
                nutrient_totals['P'] += add.p_concentration * vol_na

        # K
        if total_k > base_k:
            vol_k = required_volume_for_additive(total_k, base_k, "KCl", "k_concentration")
            if vol_k > 0:
                detailed_mix["KCl"] = vol_k
                nutrient_totals['K'] += add.k_concentration * vol_k
                nutrient_totals['Cl'] += add.cl_concentration * vol_k

        # Cl
        if total_cl > base_cl:
            vol_cl = required_volume_for_additive(total_cl, base_cl, "KCl", "cl_concentration")
            if vol_cl > 0:
                if "KCl" in detailed_mix:
                    detailed_mix["KCl"] += vol_cl
                else:
                    detailed_mix["KCl"] = vol_cl
                nutrient_totals['Cl'] += add.cl_concentration * vol_cl
                nutrient_totals['K'] += add.k_concentration * vol_cl

        # Ca
        if total_ca > base_ca:
            vol_ca = required_volume_for_additive(total_ca, base_ca, "カルチコール", "ca_concentration")
            if vol_ca > 0:
                detailed_mix["カルチコール"] = vol_ca
                nutrient_totals['Ca'] += add.ca_concentration * vol_ca

        # Mg
        if total_mg > base_mg:
            vol_mg = required_volume_for_additive(total_mg, base_mg, "カルチコール", "mg_concentration")
            if vol_mg > 0:
                if "カルチコール" in detailed_mix:
                    detailed_mix["カルチコール"] += vol_mg
                else:
                    detailed_mix["カルチコール"] = vol_mg
                nutrient_totals['Mg'] += add.mg_concentration * vol_mg

        # Zn
        if total_zn > base_zn:
            vol_zn = required_volume_for_additive(total_zn, base_zn, "プレアミンP", "zn_concentration")
            if vol_zn > 0:
                detailed_mix["プレアミンP"] = vol_zn
                nutrient_totals['Zn'] += add.zn_concentration * vol_zn

        # Amino Acids
        if total_amino_acid > nutrient_totals.get('Amino Acids', 0.0):
            diff_aa = total_amino_acid - nutrient_totals.get('Amino Acids', 0.0)
            vol_aa = diff_aa / add.amino_acid_concentration
            if vol_aa > 0:
                if "プレアミンP" in detailed_mix:
                    detailed_mix["プレアミンP"] += vol_aa
                else:
                    detailed_mix["プレアミンP"] = vol_aa
                nutrient_totals['Amino Acids'] += add.amino_acid_concentration * vol_aa

        # Fats
        if total_fat > nutrient_totals.get('Fats', 0.0):
            diff_fat = total_fat - nutrient_totals.get('Fats', 0.0)
            vol_fat = diff_fat / add.fat_concentration
            if vol_fat > 0:
                detailed_mix["イントラリポス20%"] = vol_fat
                nutrient_totals['Fats'] += add.fat_concentration * vol_fat

        # GIR用ブドウ糖液の追加
        if total_gir > 0:
            # 50%ブドウ糖液を使用
            glucose_conc = 0.5  # 50%ブドウ糖液: 0.5 g/mL
            glu_vol = total_gir / glucose_conc  # g/day / (g/mL) = mL/day
            detailed_mix["50%ブドウ糖液"] = glu_vol
            nutrient_totals['Glucose'] += glucose_conc * glu_vol

        # 添加剤が0mLの場合は削除
        detailed_mix = {k: v for k, v in detailed_mix.items() if v > 0.0}

        # 蒸留水追加
        calculated_total_volume = sum(detailed_mix.values())
        water_volume = twi_volume - calculated_total_volume
        if water_volume > 0:
            detailed_mix["蒸留水"] = water_volume

        # 栄養素合計の確認
        # 各添加剤からの栄養素が正しく加算されているか確認する
        # ここでは nutrient_totals に全て加算済みなので、再確認は不要

        # nutrient_totals の形式を確認
        # nutrient_totals = {'GIR': ..., 'Amino Acids': ..., 'Na': ..., 'K': ..., 'Cl': ..., 'Ca': ..., 'Mg': ..., 'Zn': ..., 'P': ..., 'Fats': ..., 'Glucose': ...}

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
            nutrient_units={
                'Na': 'mEq/day',
                'K': 'mEq/day',
                'Cl': 'mEq/day',
                'Ca': 'mEq/day',
                'Mg': 'mEq/day',
                'Zn': 'mmol/day',
                'P': 'mmol/day',
                'Amino Acids': 'g/day',
                'Fats': 'g/day',
                'Glucose': 'g/day',
                'GIR': 'g/day'
            },
            input_amounts=input_amounts,
            input_units=input_units
        )

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
