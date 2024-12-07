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

        # GIR計算
        if patient.gir_included and patient.gir is not None:
            total_gir = patient.gir * patient.weight * 1440 / 1000.0
            calculation_steps_list.append(f"    - **GIR計算**\n        - GIR: {patient.gir} mg/kg/min × {patient.weight} kg × 1440 min/day / 1000 = {total_gir:.2f} g/day\n")
            input_amounts['GIR'] = patient.gir
            input_units['GIR'] = "mg/kg/min"
        else:
            total_gir = 0.0
            calculation_steps_list.append("    - **GIR計算**: 計算対象外\n")

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

        twi_volume = patient.twi * patient.weight
        base_solution_volume = twi_volume
        calculation_steps += f"    - **ベース製剤 ({base_solution.name}) 計算**\n        - ベース製剤量: {base_solution_volume:.2f} mL/day\n"

        # ベース製剤からの供給量（fat_concentrationはベースにないので0とする）
        base_glucose = (base_solution.glucose_percentage / 100.0) * base_solution_volume
        base_na = base_solution.na * base_solution_volume / 1000.0
        base_k = base_solution.k * base_solution_volume / 1000.0
        base_cl = base_solution.cl * base_solution_volume / 1000.0
        base_p = base_solution.p * base_solution_volume / 1000.0
        base_mg = base_solution.mg * base_solution_volume / 1000.0
        base_ca = base_solution.ca * base_solution_volume / 1000.0
        base_zn = base_solution.zn * base_solution_volume / 1000.0
        base_fat = 0.0  # ベース製剤には脂肪なし

        calculation_steps_list2 = []
        calculation_steps += "    - **各成分の差分計算**\n"

        # 差分計算関数
        def required_volume_for_additive(total_req, base_sup, additive_name, conc_attr, conc_unit="mEq/mL"):
            if total_req > base_sup:
                diff = total_req - base_sup
                add = additives.get(additive_name)
                if not add:
                    raise ValueError(f"'{additive_name}' が添加剤に定義されていません。")
                conc = get_safe_concentration(add, conc_attr, 0.0)
                if conc == 0:
                    raise ValueError(f"{additive_name}の{conc_attr}が0です。")
                vol = diff / conc
                if vol > 0:
                    calculation_steps_list2.append(f"        - {additive_name}追加: {diff:.2f} ÷ {conc} = {vol:.2f} mL/day\n")
                    return vol
            return 0.0

        calculation_steps_list2 = []

        # 各添加剤用一時変数
        phospho_na_volume = 0.0  # リン酸Na用 Na, P
        kcl_volume = 0.0         # KCl用 K,Cl
        calcicol_volume = 0.0    # カルチコール用 Ca,Mg
        preamin_p_volume = 0.0   # プレアミンP用 Zn,アミノ酸
        intralipos20_volume = 0.0# イントラリポス20%用 Fat
        glucose_solution_volume = 0.0 # ブドウ糖用 GIR

        # Na差分->リン酸Na
        if total_na > base_na:
            diff_na = total_na - base_na
            add = additives.get("リン酸Na")
            if not add:
                raise ValueError("'リン酸Na'がありません")
            na_conc = get_safe_concentration(add, 'na_concentration')
            if na_conc == 0:
                raise ValueError("リン酸NaのNa濃度が0です")
            na_vol = diff_na / na_conc
            phospho_na_volume += na_vol
            calculation_steps_list2.append(f"        - リン酸Na(Na用): {diff_na:.2f} mEq ÷ {na_conc} mEq/mL = {na_vol:.2f} mL/day\n")

        # P差分->リン酸Na
        total_p_req = 0.0
        if patient.p_included and patient.p is not None:
            total_p_req = patient.p * patient.weight
        if total_p_req > base_p:
            diff_p = total_p_req - base_p
            add = additives.get("リン酸Na")
            if not add:
                raise ValueError("'リン酸Na'がありません")
            p_conc = get_safe_concentration(add, 'p_concentration')
            if p_conc == 0:
                raise ValueError("リン酸NaのP濃度が0です")
            p_vol = diff_p / p_conc
            phospho_na_volume += p_vol
            calculation_steps_list2.append(f"        - リン酸Na(P用): {diff_p:.2f} mmol ÷ {p_conc} mmol/mL = {p_vol:.2f} mL/day\n")

        # K差分->KCl
        if total_k > base_k:
            diff_k = total_k - base_k
            add = additives.get("KCl")
            if not add:
                raise ValueError("'KCl'がありません")
            k_conc = get_safe_concentration(add, 'k_concentration')
            if k_conc == 0:
                raise ValueError("KClのK濃度が0です")
            k_vol = diff_k / k_conc
            kcl_volume += k_vol
            calculation_steps_list2.append(f"        - KCl(K用): {diff_k:.2f} mEq ÷ {k_conc} mEq/mL = {k_vol:.2f} mL/day\n")

        # Cl差分->KCl(Clは同じKClで対応)
        if total_cl > base_cl:
            diff_cl = total_cl - base_cl
            add = additives.get("KCl")
            if not add:
                raise ValueError("'KCl'がありません")
            cl_conc = get_safe_concentration(add, 'cl_concentration')
            if cl_conc == 0:
                raise ValueError("KClのCl濃度が0です")
            cl_vol = diff_cl / cl_conc
            kcl_volume += cl_vol
            calculation_steps_list2.append(f"        - KCl(Cl用): {diff_cl:.2f} mEq ÷ {cl_conc} mEq/mL = {cl_vol:.2f} mL/day\n")

        # Ca差分->カルチコール
        if total_ca > base_ca:
            diff_ca = total_ca - base_ca
            add = additives.get("カルチコール")
            if not add:
                raise ValueError("'カルチコール'がありません")
            ca_conc = get_safe_concentration(add, 'ca_concentration')
            if ca_conc == 0:
                raise ValueError("カルチコールのCa濃度が0です")
            ca_vol = diff_ca / ca_conc
            calcicol_volume += ca_vol
            calculation_steps_list2.append(f"        - カルチコール(Ca用): {diff_ca:.2f} mEq ÷ {ca_conc} mEq/mL = {ca_vol:.2f} mL/day\n")

        # Mg差分->カルチコール
        if total_mg > base_mg:
            diff_mg = total_mg - base_mg
            add = additives.get("カルチコール")
            if not add:
                raise ValueError("'カルチコール'がありません")
            mg_conc = get_safe_concentration(add, 'mg_concentration')
            if mg_conc == 0:
                raise ValueError("カルチコールのMg濃度が0です")
            mg_vol = diff_mg / mg_conc
            calcicol_volume += mg_vol
            calculation_steps_list2.append(f"        - カルチコール(Mg用): {diff_mg:.2f} mEq ÷ {mg_conc} mEq/mL = {mg_vol:.2f} mL/day\n")

        # Zn差分->プレアミンP
        if total_zn > base_zn:
            diff_zn = total_zn - base_zn
            add = additives.get("プレアミンP")
            if not add:
                raise ValueError("'プレアミンP'がありません")
            zn_conc = get_safe_concentration(add, 'zn_concentration')
            if zn_conc == 0:
                raise ValueError("プレアミンPのZn濃度が0です")
            zn_vol = diff_zn / zn_conc
            preamin_p_volume += zn_vol
            calculation_steps_list2.append(f"        - プレアミンP(Zn用): {diff_zn:.2f} mmol ÷ {zn_conc} mmol/mL = {zn_vol:.2f} mL/day\n")

        # 脂肪差分->イントラリポス20%
        if total_fat > base_fat:
            diff_fat = total_fat - base_fat
            add = additives.get("イントラリポス20%")
            if not add:
                raise ValueError("'イントラリポス20%'がありません")
            fat_conc = get_safe_concentration(add, 'fat_concentration')
            if fat_conc == 0:
                raise ValueError("イントラリポス20%の脂肪濃度が0です")
            fat_vol = diff_fat / fat_conc
            intralipos20_volume += fat_vol
            calculation_steps_list2.append(f"        - イントラリポス20%(Fat用): {diff_fat:.2f} g ÷ {fat_conc} g/mL = {fat_vol:.2f} mL/day\n")

        # GIR用ブドウ糖->仮に50%ブドウ糖液を使用
        if total_gir > 0:
            # 50%ブドウ糖は500g/L = 0.5g/mL
            # total_girはg/day
            glucose_conc = 0.5 # 50%ブドウ糖液: 0.5 g/mL
            glu_vol = total_gir / glucose_conc
            glucose_solution_volume = glu_vol
            calculation_steps_list2.append(f"        - 50%ブドウ糖液(GIR用): {total_gir:.2f} g ÷ 0.5 g/mL = {glu_vol:.2f} mL/day\n")

        calculation_steps += "".join(calculation_steps_list2) + "\n"

        # アミノ酸->プレアミンPに統合
        if total_amino_acid > 0:
            add = additives.get("プレアミンP")
            if not add:
                raise ValueError("'プレアミンP' がありません")
            amino_acid_conc = get_safe_concentration(add, 'amino_acid_concentration')
            if amino_acid_conc == 0:
                raise ValueError("プレアミンPのアミノ酸濃度が0です")
            amino_acid_vol = total_amino_acid / amino_acid_conc
            preamin_p_volume += amino_acid_vol
            calculation_steps += f"    - **アミノ酸計算**\n        - アミノ酸濃度: {amino_acid_conc} g/mL\n        - 必要アミノ酸量: {total_amino_acid:.2f} g ÷ {amino_acid_conc} g/mL = {amino_acid_vol:.2f} mL/day\n"

        # detailed_mix構築
        detailed_mix = {}
        detailed_mix[f"ベース製剤（{base_solution.name}）"] = base_solution_volume
        if phospho_na_volume > 0:
            detailed_mix["リン酸Na"] = phospho_na_volume
        if kcl_volume > 0:
            detailed_mix["KCl"] = kcl_volume
        if calcicol_volume > 0:
            detailed_mix["カルチコール"] = calcicol_volume
        if preamin_p_volume > 0:
            detailed_mix["プレアミンP"] = preamin_p_volume
        if intralipos20_volume > 0:
            detailed_mix["イントラリポス20%"] = intralipos20_volume
        if glucose_solution_volume > 0:
            detailed_mix["50%ブドウ糖液"] = glucose_solution_volume

        # 蒸留水追加
        calculated_total_volume = sum(detailed_mix.values())
        water_volume = twi_volume - calculated_total_volume
        if water_volume > 0:
            detailed_mix["蒸留水"] = water_volume

        # 栄養素合計計算
        # 単純化のため、詳細な再計算は省略可能。必要ならここで各添加剤からの成分を再合計
        # ここでは最初の計算から変えていない前提で残す。
        nutrient_totals = {
            'Na': total_na,
            'K': total_k,
            'Cl': total_cl,
            'Ca': total_ca,
            'Mg': total_mg,
            'Zn': total_zn,
            'P': total_p_req,
            'Amino Acids': total_amino_acid,
            'Fats': total_fat,
            'Glucose': total_gir
        }

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
                'Glucose': 'g/day'
            },
            input_amounts=input_amounts,
            input_units=input_units
        )

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
