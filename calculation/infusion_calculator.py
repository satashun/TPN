# calculation/infusion_calculator.py
from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from typing import Dict
import logging

def get_safe_concentration(obj, attribute, default=0.0):
    """
    ヘルパー関数：指定された属性の値を安全に取得し、Noneの場合はデフォルト値を返す。
    """
    concentration = getattr(obj, attribute, default)
    if concentration is None:
        logging.warning(f"{attribute} for {obj.name} is None. Setting to {default}.")
        return default
    return concentration

def calculate_infusion(patient: Patient, base_solution: Solution, additives: Dict[str, Additive]) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択されたベース製剤: {base_solution}")
        logging.debug(f"選択された添加剤: {additives}")

        calculation_steps = ""
        step = 1  # メインステップ番号の初期化

        weight = patient.weight
        twi = patient.twi * weight  # 総投与量 (mL/day)
        calculation_steps += f"{step}. **総投与量 (TWI)**\n"
        calculation_steps += f"    - {patient.twi} mL/kg/day × {weight} kg = **{twi:.2f} mL/day**\n\n"
        step += 1

        gir = patient.gir if patient.gir_included else None  # mg/kg/min
        amino_acid = patient.amino_acid if patient.amino_acid_included else None  # g/kg/day
        na = patient.na if patient.na_included else None  # mEq/kg/day
        k = patient.k if patient.k_included else None  # mEq/kg/day
        p = patient.p if patient.p_included else None  # mmol/kg/day
        fat = patient.fat if patient.fat_included else None  # g/kg/day
        ca = patient.ca if patient.ca_included else None  # mEq/kg/day
        mg = patient.mg if patient.mg_included else None  # mEq/kg/day
        zn = patient.zn if patient.zn_included else None  # mmol/kg/day
        cl = patient.cl if patient.cl_included else None  # mEq/kg/day

        # 必要量の計算
        calculation_steps += f"{step}. **必要量**\n"
        step += 1

        input_amounts = {}
        input_units = {}

        if gir is not None:
            total_gir = gir * weight * 60 * 24 / 1000.0  # g/day
            calculation_steps += f"    - **GIR**\n"
            calculation_steps += f"        - {gir} mg/kg/min × {weight} kg × 60 min × 24時間 ÷ 1000 = **{total_gir:.2f} g/day**\n"
            input_amounts['GIR'] = gir
            input_units['GIR'] = "mg/kg/min"
        else:
            total_gir = 0.0
            calculation_steps += f"    - **GIR**: 計算対象外\n"

        if amino_acid is not None:
            total_amino_acid = amino_acid * weight  # g/day
            calculation_steps += f"    - **アミノ酸量**\n"
            calculation_steps += f"        - {amino_acid} g/kg/day × {weight} kg = **{total_amino_acid:.2f} g/day**\n"
            input_amounts['アミノ酸量'] = amino_acid
            input_units['アミノ酸量'] = "g/kg/day"
        else:
            total_amino_acid = 0.0
            calculation_steps += f"    - **アミノ酸量**: 計算対象外\n"

        if na is not None:
            total_na = na * weight  # mEq/day
            calculation_steps += f"    - **Na量**\n"
            calculation_steps += f"        - {na} mEq/kg/day × {weight} kg = **{total_na:.2f} mEq/day**\n"
            input_amounts['Na'] = na
            input_units['Na'] = "mEq/kg/day"
        else:
            total_na = 0.0
            calculation_steps += f"    - **Na量**: 計算対象外\n"

        if k is not None:
            total_k = k * weight  # mEq/day
            calculation_steps += f"    - **K量**\n"
            calculation_steps += f"        - {k} mEq/kg/day × {weight} kg = **{total_k:.2f} mEq/day**\n"
            input_amounts['K'] = k
            input_units['K'] = "mEq/kg/day"
        else:
            total_k = 0.0
            calculation_steps += f"    - **K量**: 計算対象外\n"

        if p is not None:
            total_p = p * weight  # mmol/day
            calculation_steps += f"    - **P量**\n"
            calculation_steps += f"        - {p} mmol/kg/day × {weight} kg = **{total_p:.2f} mmol/day**\n"
            input_amounts['P'] = p
            input_units['P'] = "mmol/kg/day"
        else:
            total_p = 0.0
            calculation_steps += f"    - **P量**: 計算対象外\n"

        if fat is not None:
            total_fat = fat * weight  # g/day
            calculation_steps += f"    - **脂肪**\n"
            calculation_steps += f"        - {fat} g/kg/day × {weight} kg = **{total_fat:.2f} g/day**\n"
            input_amounts['脂肪'] = fat
            input_units['脂肪'] = "g/kg/day"
        else:
            total_fat = 0.0
            calculation_steps += f"    - **脂肪**: 計算対象外\n"

        if ca is not None:
            total_ca = ca * weight  # mEq/day
            calculation_steps += f"    - **Ca量**\n"
            calculation_steps += f"        - {ca} mEq/kg/day × {weight} kg = **{total_ca:.2f} mEq/day**\n"
            input_amounts['Ca'] = ca
            input_units['Ca'] = "mEq/kg/day"
        else:
            total_ca = 0.0
            calculation_steps += f"    - **Ca量**: 計算対象外\n"

        if mg is not None:
            total_mg = mg * weight  # mEq/day
            calculation_steps += f"    - **Mg量**\n"
            calculation_steps += f"        - {mg} mEq/kg/day × {weight} kg = **{total_mg:.2f} mEq/day**\n"
            input_amounts['Mg'] = mg
            input_units['Mg'] = "mEq/kg/day"
        else:
            total_mg = 0.0
            calculation_steps += f"    - **Mg量**: 計算対象外\n"

        if zn is not None:
            total_zn = zn * weight  # mmol/day
            calculation_steps += f"    - **Zn量**\n"
            calculation_steps += f"        - {zn} mmol/kg/day × {weight} kg = **{total_zn:.2f} mmol/day**\n"
            input_amounts['Zn'] = zn
            input_units['Zn'] = "mmol/kg/day"
        else:
            total_zn = 0.0
            calculation_steps += f"    - **Zn量**: 計算対象外\n"

        if cl is not None:
            total_cl = cl * weight  # mEq/day
            calculation_steps += f"    - **Cl量**\n"
            calculation_steps += f"        - {cl} mEq/kg/day × {weight} kg = **{total_cl:.2f} mEq/day**\n"
            input_amounts['Cl'] = cl
            input_units['Cl'] = "mEq/kg/day"
        else:
            total_cl = 0.0
            calculation_steps += f"    - **Cl量**: 計算対象外\n"

        calculation_steps += "\n"

        # 投与計算の準備
        calculation_steps += f"{step}. **投与計算**\n"
        step += 1

        # ブドウ糖の計算
        if gir is not None and total_gir > 0:
            glucose_per_ml = get_safe_concentration(base_solution, 'glucose_percentage') / 100.0  # g/mL
            if glucose_per_ml == 0:
                raise ValueError("選択された製剤のブドウ糖濃度が0です。")
            glucose_volume = total_gir / glucose_per_ml  # mL
            calculation_steps += f"    - **ブドウ糖計算**\n"
            calculation_steps += f"        - ブドウ糖濃度: {base_solution.glucose_percentage}{base_solution.glucose_unit} (= {glucose_per_ml:.4f} g/mL)\n"
            calculation_steps += f"        - 必要ブドウ糖量: {total_gir:.2f} g/day ÷ {glucose_per_ml:.4f} g/mL = **{glucose_volume:.2f} mL**\n"
        else:
            glucose_volume = 0.0
            calculation_steps += f"    - **ブドウ糖計算**: 計算対象外\n"

        # アミノ酸の計算
        if amino_acid is not None and total_amino_acid > 0:
            if "プレアミンP" not in additives:
                raise ValueError("'プレアミンP' が additives.json に定義されていません。")
            amino_acid_additive = additives["プレアミンP"]
            amino_acid_concentration = get_safe_concentration(amino_acid_additive, 'amino_acid_concentration')
            if amino_acid_concentration == 0:
                raise ValueError("プレアミンPのアミノ酸濃度が0です。")
            amino_acid_volume = total_amino_acid / amino_acid_concentration  # mL
            calculation_steps += f"    - **アミノ酸計算**\n"
            calculation_steps += f"        - アミノ酸濃度: {amino_acid_concentration} {amino_acid_additive.amino_acid_concentration_unit}\n"
            calculation_steps += f"        - 必要アミノ酸量: {total_amino_acid:.2f} g/day ÷ {amino_acid_concentration} g/mL = **{amino_acid_volume:.2f} mL**\n"
        else:
            amino_acid_volume = 0.0
            calculation_steps += f"    - **アミノ酸計算**: 計算対象外\n"

        # Na量の計算
        if na is not None and total_na > 0:
            base_na_total = (get_safe_concentration(base_solution, 'na') * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **Na量計算**\n"
            calculation_steps += f"        - ベース製剤からのNa量: {base_solution.na} {base_solution.na_unit} × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_na_total:.2f} mEq/day**\n"
            additional_na = total_na - base_na_total  # mEq/day
            calculation_steps += f"        - 追加で必要なNa量: {total_na:.2f} mEq/day - {base_na_total:.2f} mEq/day = **{additional_na:.2f} mEq/day**\n"
        else:
            base_na_total = 0.0
            additional_na = 0.0
            calculation_steps += f"    - **Na量計算**: 計算対象外\n"

        # リン酸NaからのNa
        if na is not None and additional_na > 0:
            if "リン酸Na" not in additives:
                raise ValueError("'リン酸Na' が additives.json に定義されていません。")
            phospho_na = additives["リン酸Na"]
            na_per_ml_phospho = get_safe_concentration(phospho_na, 'na_concentration')
            if na_per_ml_phospho == 0:
                raise ValueError("リン酸NaのNa濃度が0です。")
            phospho_na_volume = additional_na / na_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのNa計算**\n"
            calculation_steps += f"        - Na濃度: {na_per_ml_phospho} {phospho_na.na_concentration_unit}\n"
            calculation_steps += f"        - 必要Na量: {additional_na:.2f} mEq/day ÷ {na_per_ml_phospho} mEq/mL = **{phospho_na_volume:.2f} mL**\n"
        else:
            phospho_na_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのNa計算**: 計算対象外\n"

        # K量の計算
        if k is not None and total_k > 0:
            base_k_total = (get_safe_concentration(base_solution, 'k') * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **K量計算**\n"
            calculation_steps += f"        - ベース製剤からのK量: {base_solution.k} {base_solution.k_unit} × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_k_total:.2f} mEq/day**\n"
            additional_k = total_k - base_k_total  # mEq/day
            calculation_steps += f"        - 追加で必要なK量: {total_k:.2f} mEq/day - {base_k_total:.2f} mEq/day = **{additional_k:.2f} mEq/day**\n"
        else:
            base_k_total = 0.0
            additional_k = 0.0
            calculation_steps += f"    - **K量計算**: 計算対象外\n"

        # KClからのK
        if k is not None and additional_k > 0:
            if "KCl" not in additives:
                raise ValueError("'KCl' が additives.json に定義されていません。")
            kcl = additives["KCl"]
            kcl_k_concentration = get_safe_concentration(kcl, 'k_concentration')
            if kcl_k_concentration == 0:
                raise ValueError("KClのK濃度が0です。")
            kcl_volume = additional_k / kcl_k_concentration  # mL
            calculation_steps += f"    - **KClからのK計算**\n"
            calculation_steps += f"        - K濃度: {kcl_k_concentration} {kcl.k_concentration_unit}\n"
            calculation_steps += f"        - 必要K量: {additional_k:.2f} mEq/day ÷ {kcl_k_concentration} mEq/mL = **{kcl_volume:.2f} mL**\n"
        else:
            kcl_volume = 0.0
            calculation_steps += f"    - **KClからのK計算**: 計算対象外\n"

        # P量の計算
        if p is not None and total_p > 0:
            if "リン酸Na" not in additives:
                raise ValueError("'リン酸Na' が additives.json に定義されていません。")
            phospho_na = additives["リン酸Na"]
            p_per_ml_phospho = get_safe_concentration(phospho_na, 'p_concentration')
            if p_per_ml_phospho == 0:
                raise ValueError("リン酸NaのP濃度が0です。")
            p_volume = total_p / p_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのP計算**\n"
            calculation_steps += f"        - P濃度: {p_per_ml_phospho} {phospho_na.p_concentration_unit}\n"
            calculation_steps += f"        - 必要P量: {total_p:.2f} mmol/day ÷ {p_per_ml_phospho} mmol/mL = **{p_volume:.2f} mL**\n"
        else:
            p_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのP計算**: 計算対象外\n"

        # 脂肪の計算
        if fat is not None and total_fat > 0:
            # 使用する脂肪添加剤の選択
            # ここでは単純にイントラリポス20%を使用する例を示します
            fat_solution = additives.get("イントラリポス20%")
            if not fat_solution:
                raise ValueError("'イントラリポス20%' が additives.json に定義されていません。")
            fat_concentration = get_safe_concentration(fat_solution, 'fat_concentration')
            if fat_concentration == 0:
                raise ValueError(f"{fat_solution.name} の脂肪濃度が0です。")
            fat_volume = total_fat / fat_concentration  # mL
            calculation_steps += f"    - **脂肪計算**\n"
            calculation_steps += f"        - 脂肪濃度: {fat_concentration} {fat_solution.fat_concentration_unit}\n"
            calculation_steps += f"        - 必要脂肪量: {total_fat:.2f} g/day ÷ {fat_concentration} g/mL = **{fat_volume:.2f} mL**\n"
        else:
            fat_volume = 0.0
            calculation_steps += f"    - **脂肪計算**: 計算対象外\n"

        # Ca量の計算
        if ca is not None and total_ca > 0:
            if "カルチコール" not in additives:
                raise ValueError("'カルチコール' が additives.json に定義されていません。")
            calc_a = additives["カルチコール"]
            ca_concentration = get_safe_concentration(calc_a, 'ca_concentration')
            if ca_concentration == 0:
                raise ValueError("カルチコールのCa濃度が0です。")
            ca_volume = total_ca / ca_concentration  # mL
            calculation_steps += f"    - **Ca量計算**\n"
            calculation_steps += f"        - Ca濃度: {ca_concentration} {calc_a.ca_concentration_unit}\n"
            calculation_steps += f"        - 必要Ca量: {total_ca:.2f} mEq/day ÷ {ca_concentration} mEq/mL = **{ca_volume:.2f} mL**\n"
        else:
            ca_volume = 0.0
            calculation_steps += f"    - **Ca量計算**: 計算対象外\n"

        # Mg量の計算
        if mg is not None and total_mg > 0:
            if "カルチコール" not in additives:
                raise ValueError("'カルチコール' が additives.json に定義されていません。")
            calc_a = additives["カルチコール"]
            mg_concentration = get_safe_concentration(calc_a, 'mg_concentration')
            if mg_concentration == 0:
                raise ValueError("カルチコールのMg濃度が0です。")
            mg_volume = total_mg / mg_concentration  # mL
            calculation_steps += f"    - **Mg量計算**\n"
            calculation_steps += f"        - Mg濃度: {mg_concentration} {calc_a.mg_concentration_unit}\n"
            calculation_steps += f"        - 必要Mg量: {total_mg:.2f} mEq/day ÷ {mg_concentration} mEq/mL = **{mg_volume:.2f} mL**\n"
        else:
            mg_volume = 0.0
            calculation_steps += f"    - **Mg量計算**: 計算対象外\n"

        # Zn量の計算
        if zn is not None and total_zn > 0:
            if "プレアミンP" not in additives:
                raise ValueError("'プレアミンP' が additives.json に定義されていません。")
            pa_p = additives["プレアミンP"]
            zn_concentration = get_safe_concentration(pa_p, 'zn_concentration')
            if zn_concentration == 0:
                raise ValueError("プレアミンPのZn濃度が0です。")
            zn_volume = total_zn / zn_concentration  # mL
            calculation_steps += f"    - **Zn量計算**\n"
            calculation_steps += f"        - Zn濃度: {zn_concentration} {pa_p.zn_concentration_unit}\n"
            calculation_steps += f"        - 必要Zn量: {total_zn:.2f} mmol/day ÷ {zn_concentration} mmol/mL = **{zn_volume:.2f} mL**\n"
        else:
            zn_volume = 0.0
            calculation_steps += f"    - **Zn量計算**: 計算対象外\n"

        # Cl量の計算
        if cl is not None and total_cl > 0:
            base_cl_total = (get_safe_concentration(base_solution, 'cl') * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **Cl量計算**\n"
            calculation_steps += f"        - ベース製剤からのCl量: {base_solution.cl} {base_solution.cl_unit} × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_cl_total:.2f} mEq/day**\n"
            additional_cl = total_cl - base_cl_total  # mEq/day
            calculation_steps += f"        - 追加で必要なCl量: {total_cl:.2f} mEq/day - {base_cl_total:.2f} mEq/day = **{additional_cl:.2f} mEq/day**\n"
        else:
            base_cl_total = 0.0
            additional_cl = 0.0
            calculation_steps += f"    - **Cl量計算**: 計算対象外\n"

        # 生理食塩水からのCl
        if cl is not None and additional_cl > 0:
            if "生理食塩水" not in additives:
                raise ValueError("'生理食塩水' が additives.json に定義されていません。")
            saline = additives["生理食塩水"]
            cl_per_ml_saline = get_safe_concentration(saline, 'cl_concentration')
            if cl_per_ml_saline == 0:
                raise ValueError("生理食塩水のCl濃度が0です。")
            saline_volume = additional_cl / cl_per_ml_saline  # mL
            calculation_steps += f"    - **生理食塩水からのCl計算**\n"
            calculation_steps += f"        - Cl濃度: {cl_per_ml_saline} {saline.cl_concentration_unit}\n"
            calculation_steps += f"        - 必要Cl量: {additional_cl:.2f} mEq/day ÷ {cl_per_ml_saline} mEq/mL = **{saline_volume:.2f} mL**\n"
        else:
            saline_volume = 0.0
            calculation_steps += f"    - **生理食塩水からのCl計算**: 計算対象外\n"

        calculation_steps += "\n"

        # 総液量の計算
        calculation_steps += f"{step}. **総液量計算**\n"
        step += 1
        calculated_total_volume = (
            glucose_volume +
            amino_acid_volume +
            phospho_na_volume +
            kcl_volume +
            p_volume +
            fat_volume +
            ca_volume +
            mg_volume +
            zn_volume +
            saline_volume
        )
        calculation_steps += f"    - 総液量: {glucose_volume:.2f} + {amino_acid_volume:.2f} + {phospho_na_volume:.2f} + {kcl_volume:.2f} + {p_volume:.2f} + {fat_volume:.2f} + {ca_volume:.2f} + {mg_volume:.2f} + {zn_volume:.2f} + {saline_volume:.2f} = **{calculated_total_volume:.2f} mL**\n"
        water_volume = twi - calculated_total_volume  # mL
        calculation_steps += f"    - 必要水量: {twi:.2f} mL/day - {calculated_total_volume:.2f} mL/day = **{water_volume:.2f} mL/day**\n\n"
        step += 1

        # 蒸留水の量は水量が負になる場合は0にする
        final_water_volume = max(water_volume, 0.0)
        if water_volume < 0:
            calculation_steps += f"{step}. **警告** ⚠️\n"
            calculation_steps += f"    - 総液量がTWIを超過しています。製剤の配合を見直してください。\n\n"
            raise ValueError("総液量がTWIを超過しています。製剤の配合を見直してください。")
        calculation_steps += f"{step}. **蒸留水の量**\n"
        calculation_steps += f"    - max({water_volume:.2f}, 0) = **{final_water_volume:.2f} mL/day**\n\n"
        step += 1

        # 配合量の詳細を保存
        calculation_steps += f"{step}. **配合量の詳細**\n"
        step += 1
        detailed_mix = {}
        if glucose_volume > 0:
            detailed_mix[base_solution.name] = glucose_volume
        if amino_acid_volume > 0:
            detailed_mix["プレアミンP"] = amino_acid_volume
        if phospho_na_volume > 0:
            if "リン酸Na" in detailed_mix:
                detailed_mix["リン酸Na"] += phospho_na_volume
            else:
                detailed_mix["リン酸Na"] = phospho_na_volume
        if kcl_volume > 0:
            detailed_mix["KCl"] = kcl_volume
        if p_volume > 0:
            if "リン酸Na" in detailed_mix:
                detailed_mix["リン酸Na"] += p_volume
            else:
                detailed_mix["リン酸Na"] = p_volume
        if fat_volume > 0:
            detailed_mix[fat_solution.name] = fat_volume
        if ca_volume > 0:
            detailed_mix["カルチコール"] = ca_volume
        if mg_volume > 0:
            if "カルチコール" in detailed_mix:
                detailed_mix["カルチコール"] += mg_volume
            else:
                detailed_mix["カルチコール"] = mg_volume
        if zn_volume > 0:
            if "プレアミンP" in detailed_mix:
                detailed_mix["プレアミンP"] += zn_volume
            else:
                detailed_mix["プレアミンP"] = zn_volume
        if saline_volume > 0:
            detailed_mix["生理食塩水"] = saline_volume
        if final_water_volume > 0:
            detailed_mix["蒸留水"] = final_water_volume

        calculation_steps += f"    - **配合量の詳細:**\n"
        for key, value in detailed_mix.items():
            calculation_steps += f"        - {key}: {value:.2f} mL/day\n"

        calculation_steps += "\n"

        # 各栄養素の最終溶液中の量を計算
        nutrient_totals = {}
        nutrient_units = {
            'Na': 'mEq/day',
            'K': 'mEq/day',
            'Ca': 'mEq/day',
            'P': 'mmol/day',
            'Mg': 'mEq/day',
            'Zn': 'mmol/day',
            'Cl': 'mEq/day',
            'Amino Acids': 'g/day',
            'Fats': 'g/day',
            'Glucose': 'g/day'
        }

        # 初期化
        for nutrient in nutrient_units.keys():
            nutrient_totals[nutrient] = 0.0

        # 計算
        for sol_name, vol in detailed_mix.items():
            if sol_name == base_solution.name:
                # ベース製剤からの栄養素
                nutrient_totals['Na'] += base_solution.na * vol / 1000.0  # mEq/L to mEq/mL
                nutrient_totals['K'] += base_solution.k * vol / 1000.0
                nutrient_totals['Cl'] += base_solution.cl * vol / 1000.0
                nutrient_totals['P'] += base_solution.p * vol / 1000.0
                nutrient_totals['Glucose'] += (base_solution.glucose_percentage * vol) / 100.0  # g/L to g/mL
                nutrient_totals['Mg'] += base_solution.mg * vol / 1000.0
                nutrient_totals['Ca'] += base_solution.ca * vol / 1000.0
                nutrient_totals['Zn'] += base_solution.zn * vol / 1000.0
            else:
                additive = additives.get(sol_name)
                if additive:
                    # 各添加剤からの栄養素
                    if additive.na_concentration > 0:
                        nutrient_totals['Na'] += additive.na_concentration * vol
                    if additive.k_concentration > 0:
                        nutrient_totals['K'] += additive.k_concentration * vol
                    if additive.ca_concentration > 0:
                        nutrient_totals['Ca'] += additive.ca_concentration * vol
                    if additive.p_concentration > 0:
                        nutrient_totals['P'] += additive.p_concentration * vol
                    if additive.mg_concentration > 0:
                        nutrient_totals['Mg'] += additive.mg_concentration * vol
                    if additive.zn_concentration > 0:
                        nutrient_totals['Zn'] += additive.zn_concentration * vol
                    if additive.cl_concentration > 0:
                        nutrient_totals['Cl'] += additive.cl_concentration * vol
                    if additive.amino_acid_concentration > 0:
                        nutrient_totals['Amino Acids'] += additive.amino_acid_concentration * vol
                    if additive.fat_concentration > 0:
                        nutrient_totals['Fats'] += additive.fat_concentration * vol
                    # ブドウ糖が含まれている場合は追加
                    if hasattr(additive, 'glucose_percentage') and getattr(additive, 'glucose_percentage', 0) > 0:
                        nutrient_totals['Glucose'] += (additive.glucose_percentage * vol) / 100.0  # % to g/mL

        # kg単位での計算
        nutrient_per_kg = {nutrient: total / weight for nutrient, total in nutrient_totals.items()}

        # 計算ステップに追加
        calculation_steps += f"{step}. **最終溶液中の各栄養素の量**\n"
        step += 1
        calculation_steps += f"    - 以下に各栄養素の最終溶液中の量を示します。\n"

        calculation_steps += f"    | 栄養素 | 入力量 | 入力単位 | 最終溶液中の量 | 最終溶液中の量単位 | 最終溶液中の量 (kg単位) | 最終溶液中の量 (kg単位) 単位 |\n"
        calculation_steps += f"    |---|---|---|---|---|---|---|\n"
        for nutrient in nutrient_units.keys():
            input_amount = input_amounts.get(nutrient, 0.0)
            input_unit = input_units.get(nutrient, "")
            total = nutrient_totals[nutrient]
            per_kg = nutrient_per_kg[nutrient]
            per_kg_unit = nutrient_units[nutrient].replace('/day', '/day/kg')
            calculation_steps += f"    | {nutrient} | {input_amount:.2f} | {input_unit} | {total:.2f} | {nutrient_units[nutrient]} | {per_kg:.2f} | {per_kg_unit} |\n"

        # 計算結果の作成
        infusion_mix = InfusionMix(
            gir=gir,
            amino_acid=amino_acid,
            na=na,
            k=k,
            p=p,
            fat=fat,
            ca=ca,
            mg=mg,
            zn=zn,
            cl=cl,
            detailed_mix=detailed_mix,
            calculation_steps=calculation_steps,
            nutrient_totals=nutrient_totals,
            nutrient_units=nutrient_units,
            input_amounts=input_amounts,
            input_units=input_units
        )

        logging.debug(f"計算ステップ: {calculation_steps}")
        logging.debug(f"配合量の詳細: {detailed_mix}")
        logging.debug(f"栄養素の総量: {nutrient_totals}")
        logging.debug(f"栄養素の単位: {nutrient_units}")
        logging.debug(f"入力量: {input_amounts}")
        logging.debug(f"入力単位: {input_units}")

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
