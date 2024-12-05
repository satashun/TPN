# calculation.py
from models import Patient, Solution, InfusionMix
import logging

def calculate_infusion(patient: Patient, solution: Solution) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択された製剤: {solution}")

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
            calculation_steps += f"        - {na} mEq/kg/day × {weight} kg = **{total_na:.2f} mEq/day**\n"
        else:
            total_na = 0.0
            calculation_steps += f"    - **Na量**: 計算対象外\n"

        if k is not None:
            total_k = k * weight  # mEq/day
            calculation_steps += f"    - **K量**\n"
            calculation_steps += f"        - {k} mEq/kg/day × {weight} kg = **{total_k:.2f} mEq/day**\n"
        else:
            total_k = 0.0
            calculation_steps += f"    - **K量**: 計算対象外\n"

        if p is not None:
            total_p = p * weight  # mmol/day
            calculation_steps += f"    - **P量**\n"
            calculation_steps += f"        - {p} mmol/kg/day × {weight} kg = **{total_p:.2f} mmol/day**\n"
        else:
            total_p = 0.0
            calculation_steps += f"    - **P量**: 計算対象外\n"

        calculation_steps += "\n"

        # 投与計算の準備
        calculation_steps += f"{step}. **投与計算**\n"
        step += 1

        # ブドウ糖の計算
        if gir is not None and total_gir > 0:
            glucose_per_ml = solution.glucose_percentage / 100.0  # g/mL
            if glucose_per_ml == 0:
                raise ValueError("選択された製剤のブドウ糖濃度が0です。")
            glucose_volume = total_gir / glucose_per_ml  # mL
            calculation_steps += f"    - **ブドウ糖計算**\n"
            calculation_steps += f"        - ブドウ糖濃度: {solution.glucose_percentage}% (= {glucose_per_ml} g/mL)\n"
            calculation_steps += f"        - 必要ブドウ糖量: {total_gir:.2f} g/day ÷ {glucose_per_ml} g/mL = **{glucose_volume:.2f} mL**\n"
        else:
            glucose_volume = 0.0
            calculation_steps += f"    - **ブドウ糖計算**: 計算対象外\n"

        # アミノ酸の計算
        if amino_acid is not None and total_amino_acid > 0:
            amino_acid_concentration = 76.0 / 1000.0  # g/mL
            if amino_acid_concentration == 0:
                raise ValueError("プレアミンPのアミノ酸濃度が0です。")
            amino_acid_volume = total_amino_acid / amino_acid_concentration  # mL
            calculation_steps += f"    - **アミノ酸計算**\n"
            calculation_steps += f"        - アミノ酸濃度: {amino_acid_concentration} g/mL\n"
            calculation_steps += f"        - 必要アミノ酸量: {total_amino_acid:.2f} g/day ÷ {amino_acid_concentration} g/mL = **{amino_acid_volume:.2f} mL**\n"
        else:
            amino_acid_volume = 0.0
            calculation_steps += f"    - **アミノ酸計算**: 計算対象外\n"

        # Na量の計算
        if na is not None and total_na > 0:
            base_na_total = (solution.na * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **Na量計算**\n"
            calculation_steps += f"        - ベース製剤からのNa量: {solution.na} mEq/L × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_na_total:.2f} mEq/day**\n"
            additional_na = total_na - base_na_total  # mEq/day
            calculation_steps += f"        - 追加で必要なNa量: {total_na:.2f} mEq/day - {base_na_total:.2f} mEq/day = **{additional_na:.2f} mEq/day**\n"
        else:
            base_na_total = 0.0
            additional_na = 0.0
            calculation_steps += f"    - **Na量計算**: 計算対象外\n"

        # リン酸NaからのNa
        if na is not None and additional_na > 0:
            na_per_ml_phospho = 15.0 / 20.0  # mEq/mL
            if na_per_ml_phospho == 0:
                raise ValueError("リン酸NaのNa濃度が0です。")
            phospho_na_volume = additional_na / na_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのNa計算**\n"
            calculation_steps += f"        - Na濃度: {na_per_ml_phospho} mEq/mL\n"
            calculation_steps += f"        - 必要Na量: {additional_na:.2f} mEq/day ÷ {na_per_ml_phospho} mEq/mL = **{phospho_na_volume:.2f} mL**\n"
        else:
            phospho_na_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのNa計算**: 計算対象外\n"

        # K量の計算
        if k is not None and total_k > 0:
            base_k_total = (solution.k * glucose_volume) / 1000.0  # mEq/day
            calculation_steps += f"    - **K量計算**\n"
            calculation_steps += f"        - ベース製剤からのK量: {solution.k} mEq/L × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_k_total:.2f} mEq/day**\n"
            additional_k = total_k - base_k_total  # mEq/day
            calculation_steps += f"        - 追加で必要なK量: {total_k:.2f} mEq/day - {base_k_total:.2f} mEq/day = **{additional_k:.2f} mEq/day**\n"
        else:
            base_k_total = 0.0
            additional_k = 0.0
            calculation_steps += f"    - **K量計算**: 計算対象外\n"

        # KClからのK
        if k is not None and additional_k > 0:
            kcl_k_concentration = 1.0  # mEq/mL
            if kcl_k_concentration == 0:
                raise ValueError("KClのK濃度が0です。")
            kcl_volume = additional_k / kcl_k_concentration  # mL
            calculation_steps += f"    - **KClからのK計算**\n"
            calculation_steps += f"        - K濃度: {kcl_k_concentration} mEq/mL\n"
            calculation_steps += f"        - 必要K量: {additional_k:.2f} mEq/day ÷ {kcl_k_concentration} mEq/mL = **{kcl_volume:.2f} mL**\n"
        else:
            kcl_volume = 0.0
            calculation_steps += f"    - **KClからのK計算**: 計算対象外\n"

        # P量の計算
        if p is not None and total_p > 0:
            p_per_ml_phospho = 10.0 / 20.0  # mmol/mL
            if p_per_ml_phospho == 0:
                raise ValueError("リン酸NaのP濃度が0です。")
            p_volume = total_p / p_per_ml_phospho  # mL
            calculation_steps += f"    - **リン酸NaからのP計算**\n"
            calculation_steps += f"        - P濃度: {p_per_ml_phospho} mmol/mL\n"
            calculation_steps += f"        - 必要P量: {total_p:.2f} mmol/day ÷ {p_per_ml_phospho} mmol/mL = **{p_volume:.2f} mL**\n"
        else:
            p_volume = 0.0
            calculation_steps += f"    - **リン酸NaからのP計算**: 計算対象外\n"

        calculation_steps += "\n"

        # 総液量の計算
        calculation_steps += f"{step}. **総液量計算**\n"
        step += 1
        calculated_total_volume = glucose_volume + amino_acid_volume + phospho_na_volume + kcl_volume + p_volume
        calculation_steps += f"    - 総液量: {glucose_volume:.2f} + {amino_acid_volume:.2f} + {phospho_na_volume:.2f} + {kcl_volume:.2f} + {p_volume:.2f} = **{calculated_total_volume:.2f} mL**\n"
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
        detailed_mix = {
            "ソルデム3AG": glucose_volume,
            "プレアミンP": amino_acid_volume,
            "リン酸Na": p_volume,
            "KCl": kcl_volume,
            "蒸留水": final_water_volume
        }
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
            detailed_mix=detailed_mix,
            calculation_steps=calculation_steps
        )

        logging.info("計算完了")
        return infusion_mix

    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
