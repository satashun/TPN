# calculation.py
from models import Patient, Solution, Additive, InfusionMix
from typing import Dict
import logging

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
        calculation_steps += f"    - {patient.twi} {base_solution.glucose_unit}/kg/day × {weight} kg = **{twi:.2f} mL/day**\n\n"
        step += 1

        gir = patient.gir if patient.gir_included else None  # mg/kg/min
        amino_acid = patient.amino_acid if patient.amino_acid_included else None  # g/kg/day
        na = patient.na if patient.na_included else None  # mEq/kg/day
        k = patient.k if patient.k_included else None  # mEq/kg/day
        p = patient.p if patient.p_included else None  # mmol/kg/day
        fat = patient.fat if patient.fat_included else None  # g/kg/day
        ca = patient.ca if patient.ca_included else None  # mEq/kg/day

        # 必要量の計算
        calculation_steps += f"{step}. **必要量**\n"
        step += 1

        if gir is not None:
            total_gir = gir * weight * 60 * 24 / 1000  # g/day
            calculation_steps += f"    - **GIR**\n"
            calculation_steps += f"        - {gir} mg/kg/min × {weight} kg × 60 min × 24時間 ÷ 1000 = **{total_gir:.2f} g/day**\n"
        else:
            total_gir = 0.0
            calculation_steps += f"    - **GIR**: 計算対象外\n"

        if amino_acid is not None:
            total_amino_acid = amino_acid * weight  # g/day
            calculation_steps += f"    - **アミノ酸量**\n"
            calculation_steps += f"        - {amino_acid} g/kg/day × {weight} kg = **{total_amino_acid:.2f} g/day**\n"
        else:
            total_amino_acid = 0.0
            calculation_steps += f"    - **アミノ酸量**: 計算対象外\n"

        if na is not None:
            total_na = na * weight  # mEq/day
            calculation_steps += f"    - **Na量**\n"
            calculation_steps += f"        - {na} {base_solution.na_unit}/kg/day × {weight} kg = **{total_na:.2f} {base_solution.na_unit}/day**\n"
        else:
            total_na = 0.0
            calculation_steps += f"    - **Na量**: 計算対象外\n"

        if k is not None:
            total_k = k * weight  # mEq/day
            calculation_steps += f"    - **K量**\n"
            calculation_steps += f"        - {k} {base_solution.k_unit}/kg/day × {weight} kg = **{total_k:.2f} {base_solution.k_unit}/day**\n"
        else:
            total_k = 0.0
            calculation_steps += f"    - **K量**: 計算対象外\n"

        if p is not None:
            total_p = p * weight  # mmol/day
            calculation_steps += f"    - **P量**\n"
            calculation_steps += f"        - {p} {base_solution.p_unit}/kg/day × {weight} kg = **{total_p:.2f} {base_solution.p_unit}/day**\n"
        else:
            total_p = 0.0
            calculation_steps += f"    - **P量**: 計算対象外\n"

        if fat is not None:
            total_fat = fat * weight  # g/day
            calculation_steps += f"    - **脂肪**\n"
            calculation_steps += f"        - {fat} {base_solution.calories_unit}/kg/day × {weight} kg = **{total_fat:.2f} g/day**\n"
        else:
            total_fat = 0.0
            calculation_steps += f"    - **脂肪**: 計算対象外\n"

        if ca is not None:
            total_ca = ca * weight  # mEq/day
            calculation_steps += f"    - **Ca量**\n"
            calculation_steps += f"        - {ca} {base_solution.calories_unit}/kg/day × {weight} kg = **{total_ca:.2f} {base_solution.calories_unit}/day**\n"
        else:
            total_ca = 0.0
            calculation_steps += f"    - **Ca量**: 計算対象外\n"

        calculation_steps += "\n"

        # 投与計算の準備
        calculation_steps += f"{step}. **投与計算**\n"
        step += 1

        # ブドウ糖の計算
        if gir is not None and total_gir > 0:
            glucose_per_ml = base_solution.glucose_percentage / 100.0  # g/mL
            if glucose_per_ml == 0:
                raise ValueError("選択された製剤のブドウ糖濃度が0です。")
            glucose_volume = total_gir / glucose_per_ml  # mL
            calculation_steps += f"    - **ブドウ糖計算**\n"
            calculation_steps += f"        - ブドウ糖濃度: {base_solution.glucose_percentage}{base_solution.glucose_unit} (= {glucose_per_ml} g/mL)\n"
            calculation_steps += f"        - 必要ブドウ糖量: {total_gir:.2f} g/day ÷ {glucose_per_ml} g/mL = **{glucose_volume:.2f} mL**\n"
        else:
            glucose_volume = 0.0
            calculation_steps += f"    - **ブドウ糖計算**: 計算対象外\n"

        # アミノ酸の計算
        if amino_acid is not None and total_amino_acid > 0:
            if "プレアミンP" not in additives:
                raise ValueError("'プレアミンP' が additives.json に定義されていません。")
            amino_acid_concentration = additives["プレアミンP"].na_concentration  # g/mL
            if amino_acid_concentration == 0:
                raise ValueError("プレアミンPのアミノ酸濃度が0です。")
            amino_acid_volume = total_amino_acid / amino_acid_concentration  # mL
            calculation_steps += f"    - **アミノ酸計算**\n"
            calculation_steps += f"        - アミノ酸濃度: {amino_acid_concentration} {additives['プレアミンP'].na_concentration_unit}\n"
            calculation_steps += f"        - 必要アミノ酸量: {total_amino_acid:.2f} g/day ÷ {amino_acid_concentration} g/mL = **{amino_acid_volume:.2f} mL**\n"
        else:
            amino_acid_volume = 0.0
            calculation_steps += f"    - **アミノ酸計算**: 計算対象外\n"

        # Na量の計算
        if na is not None and total_na > 0:
            base_na_total = (base_solution.na * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **Na量計算**\n"
            calculation_steps += f"        - ベース製剤からのNa量: {base_solution.na} {base_solution.na_unit} × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_na_total:.2f} {base_solution.na_unit}/day**\n"
            additional_na = total_na - base_na_total  # mEq/day
            calculation_steps += f"        - 追加で必要なNa量: {total_na:.2f} {base_solution.na_unit}/day - {base_na_total:.2f} {base_solution.na_unit}/day = **{additional_na:.2f} {base_solution.na_unit}/day**\n"
        else:
            base_na_total = 0.0
            additional_na = 0.0
            calculation_steps += f"    - **Na量計算**: 計算対象外\n"

        # リン酸NaからのNa
        if na is not None and additional_na > 0:
            if "リン酸Na" not in additives:
                raise ValueError("'リン酸Na' が additives.json に定義されていません。")
            phospho_na = additives["リン酸Na"]
            na_per_ml_phospho = phospho_na.na_concentration  # mEq/mL
            if na_per_ml_phospho == 0:
                raise ValueError("リン酸NaのNa濃度が0です。")
            phospho_na_volume = additional_na / na_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのNa計算**\n"
            calculation_steps += f"        - Na濃度: {na_per_ml_phospho} {phospho_na.na_concentration_unit}\n"
            calculation_steps += f"        - 必要Na量: {additional_na:.2f} {base_solution.na_unit}/day ÷ {na_per_ml_phospho} mEq/mL = **{phospho_na_volume:.2f} mL**\n"
        else:
            phospho_na_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのNa計算**: 計算対象外\n"

        # K量の計算
        if k is not None and total_k > 0:
            base_k_total = (base_solution.k * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **K量計算**\n"
            calculation_steps += f"        - ベース製剤からのK量: {base_solution.k} {base_solution.k_unit} × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_k_total:.2f} {base_solution.k_unit}/day**\n"
            additional_k = total_k - base_k_total  # mEq/day
            calculation_steps += f"        - 追加で必要なK量: {total_k:.2f} {base_solution.k_unit}/day - {base_k_total:.2f} {base_solution.k_unit}/day = **{additional_k:.2f} {base_solution.k_unit}/day**\n"
        else:
            base_k_total = 0.0
            additional_k = 0.0
            calculation_steps += f"    - **K量計算**: 計算対象外\n"

        # KClからのK
        if k is not None and additional_k > 0:
            if "KCl" not in additives:
                raise ValueError("'KCl' が additives.json に定義されていません。")
            kcl = additives["KCl"]
            kcl_k_concentration = kcl.na_concentration  # mEq/mL
            if kcl_k_concentration == 0:
                raise ValueError("KClのK濃度が0です。")
            kcl_volume = additional_k / kcl_k_concentration  # mL
            calculation_steps += f"    - **KClからのK計算**\n"
            calculation_steps += f"        - K濃度: {kcl_k_concentration} {kcl.na_concentration_unit}\n"
            calculation_steps += f"        - 必要K量: {additional_k:.2f} {base_solution.k_unit}/day ÷ {kcl_k_concentration} mEq/mL = **{kcl_volume:.2f} mL**\n"
        else:
            kcl_volume = 0.0
            calculation_steps += f"    - **KClからのK計算**: 計算対象外\n"

        # P量の計算
        if p is not None and total_p > 0:
            if "リン酸Na" not in additives:
                raise ValueError("'リン酸Na' が additives.json に定義されていません。")
            phospho_na = additives["リン酸Na"]
            p_per_ml_phospho = phospho_na.p_concentration  # mmol/mL
            if p_per_ml_phospho == 0:
                raise ValueError("リン酸NaのP濃度が0です。")
            p_volume = total_p / p_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのP計算**\n"
            calculation_steps += f"        - P濃度: {p_per_ml_phospho} {phospho_na.p_concentration_unit}\n"
            calculation_steps += f"        - 必要P量: {total_p:.2f} {base_solution.p_unit}/day ÷ {p_per_ml_phospho} mmol/mL = **{p_volume:.2f} mL**\n"
        else:
            p_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのP計算**: 計算対象外\n"

        # 脂肪の計算
        if fat is not None and total_fat > 0:
            if "イントラリポス" not in additives:
                raise ValueError("'イントラリポス' が additives.json に定義されていません。")
            fat_solution = additives["イントラリポス"]
            fat_concentration = fat_solution.fat_concentration  # g/mL
            if fat_concentration == 0:
                raise ValueError("イントラリポスの脂肪濃度が0です。")
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
            ca_concentration = calc_a.ca_concentration  # mEq/mL
            if ca_concentration == 0:
                raise ValueError("カルチコールのCa濃度が0です。")
            ca_volume = total_ca / ca_concentration  # mL
            calculation_steps += f"    - **Ca量計算**\n"
            calculation_steps += f"        - Ca濃度: {ca_concentration} {calc_a.ca_concentration_unit}\n"
            calculation_steps += f"        - 必要Ca量: {total_ca:.2f} {base_solution.calories_unit}/day ÷ {ca_concentration} mEq/mL = **{ca_volume:.2f} mL**\n"
        else:
            ca_volume = 0.0
            calculation_steps += f"    - **Ca量計算**: 計算対象外\n"

        calculation_steps += "\n"

        # 総液量の計算
        calculation_steps += f"{step}. **総液量計算**\n"
        step += 1
        calculated_total_volume = glucose_volume + amino_acid_volume + phospho_na_volume + kcl_volume + p_volume + fat_volume + ca_volume
        calculation_steps += f"    - 総液量: {glucose_volume:.2f} + {amino_acid_volume:.2f} + {phospho_na_volume:.2f} + {kcl_volume:.2f} + {p_volume:.2f} + {fat_volume:.2f} + {ca_volume:.2f} = **{calculated_total_volume:.2f} mL**\n"
        water_volume = twi - calculated_total_volume  # mL
        calculation_steps += f"    - 必要水量: {twi:.2f} mL/day - {calculated_total_volume:.2f} mL/day = **{water_volume:.2f} mL/day**\n\n"

        # 蒸留水の量は水量が負になる場合は0にする
        final_water_volume = max(water_volume, 0)
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
            detailed_mix["イントラリポス"] = fat_volume
        if ca_volume > 0:
            detailed_mix["カルチコール"] = ca_volume
        if final_water_volume > 0:
            detailed_mix["蒸留水"] = final_water_volume

        for key, value in detailed_mix.items():
            calculation_steps += f"    - {key}: {value:.2f} mL/day\n"

        logging.debug(f"計算ステップ: {calculation_steps}")
        logging.debug(f"配合量の詳細: {detailed_mix}")

        # 計算結果の作成
        infusion_mix = InfusionMix(
            gir=gir,
            amino_acid=amino_acid,
            na=na,
            k=k,
            p=p,
            fat=fat,
            ca=ca,
            detailed_mix=detailed_mix,
            calculation_steps=calculation_steps
        )

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
