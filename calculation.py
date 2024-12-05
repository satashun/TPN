# calculation.py
from models import Patient, Solution, InfusionMix
import logging

def calculate_infusion(patient: Patient, solution: Solution) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択された製剤: {solution}")

        calculation_steps = ""

        weight = patient.weight
        twi = patient.twi * weight  # 総投与量 (mL/day)
        calculation_steps += f"1. **総投与量 (TWI)**: {patient.twi} mL/kg/day × {weight} kg = **{twi:.2f} mL/day**\n"

        gir = patient.gir  # mg/kg/min
        amino_acid = patient.amino_acid  # g/kg/day
        na = patient.na  # mEq/kg/day
        k = patient.k  # mEq/kg/day
        p = patient.p  # mmol/kg/day

        # 必要量の計算
        total_gir = gir * weight * 60 * 24 / 1000  # g/day
        calculation_steps += f"\n2. **必要GIR**: {gir} mg/kg/min × {weight} kg × 60 min × 24時間 ÷ 1000 = **{total_gir:.2f} g/day**\n"

        total_amino_acid = amino_acid * weight  # g/day
        calculation_steps += f"3. **必要アミノ酸量**: {amino_acid} g/kg/day × {weight} kg = **{total_amino_acid:.2f} g/day**\n"

        total_na = na * weight  # mEq/day
        calculation_steps += f"4. **必要Na量**: {na} mEq/kg/day × {weight} kg = **{total_na:.2f} mEq/day**\n"

        total_k = k * weight  # mEq/day
        calculation_steps += f"5. **必要K量**: {k} mEq/kg/day × {weight} kg = **{total_k:.2f} mEq/day**\n"

        total_p = p * weight  # mmol/day
        calculation_steps += f"6. **必要P量**: {p} mmol/kg/day × {weight} kg = **{total_p:.2f} mmol/day**\n"

        # ブドウ糖の計算
        glucose_per_ml = solution.glucose_percentage / 100.0  # g/mL
        if glucose_per_ml == 0:
            raise ValueError("選択された製剤のブドウ糖濃度が0です。")
        glucose_volume = total_gir / glucose_per_ml  # mL
        calculation_steps += f"\n7. **ブドウ糖濃度**: {solution.glucose_percentage}% (={glucose_per_ml} g/mL)\n"
        calculation_steps += f"   **必要ブドウ糖量**: {total_gir:.2f} g/day ÷ {glucose_per_ml} g/mL = **{glucose_volume:.2f} mL**\n"

        # アミノ酸の計算
        amino_acid_concentration = 76.0 / 1000.0  # g/mL
        if amino_acid_concentration == 0:
            raise ValueError("プレアミンPのアミノ酸濃度が0です。")
        amino_acid_volume = total_amino_acid / amino_acid_concentration  # mL
        calculation_steps += f"\n8. **アミノ酸濃度**: {amino_acid_concentration} g/mL\n"
        calculation_steps += f"   **必要アミノ酸量**: {total_amino_acid:.2f} g/day ÷ {amino_acid_concentration} g/mL = **{amino_acid_volume:.2f} mL**\n"

        # Na量の計算
        base_na_total = (solution.na * glucose_volume) / 1000.0  # mEq/day
        calculation_steps += f"\n9. **ベース製剤からのNa量**: {solution.na} mEq/L × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_na_total:.2f} mEq/day**\n"
        additional_na = total_na - base_na_total  # mEq/day
        calculation_steps += f"   **追加で必要なNa量**: {total_na:.2f} mEq/day - {base_na_total:.2f} mEq/day = **{additional_na:.2f} mEq/day**\n"

        # リン酸NaからのNa
        na_per_ml_phospho = 15.0 / 20.0  # mEq/mL
        if na_per_ml_phospho == 0:
            raise ValueError("リン酸NaのNa濃度が0です。")
        phospho_na_volume = additional_na / na_per_ml_phospho  # mL
        calculation_steps += f"\n10. **リン酸NaからのNa濃度**: {na_per_ml_phospho} mEq/mL\n"
        calculation_steps += f"    **必要Na量**: {additional_na:.2f} mEq/day ÷ {na_per_ml_phospho} mEq/mL = **{phospho_na_volume:.2f} mL**\n"

        # K量の計算
        base_k_total = (solution.k * glucose_volume) / 1000.0  # mEq/day
        calculation_steps += f"\n11. **ベース製剤からのK量**: {solution.k} mEq/L × {glucose_volume:.2f} mL/day ÷ 1000 = **{base_k_total:.2f} mEq/day**\n"
        additional_k = total_k - base_k_total  # mEq/day
        calculation_steps += f"    **追加で必要なK量**: {total_k:.2f} mEq/day - {base_k_total:.2f} mEq/day = **{additional_k:.2f} mEq/day**\n"

        # KClからのK
        kcl_k_concentration = 1.0  # mEq/mL
        if kcl_k_concentration == 0:
            raise ValueError("KClのK濃度が0です。")
        kcl_volume = additional_k / kcl_k_concentration  # mL
        calculation_steps += f"\n12. **KClからのK濃度**: {kcl_k_concentration} mEq/mL\n"
        calculation_steps += f"    **必要K量**: {additional_k:.2f} mEq/day ÷ {kcl_k_concentration} mEq/mL = **{kcl_volume:.2f} mL**\n"

        # P量の計算
        p_per_ml_phospho = 10.0 / 20.0  # mmol/mL
        if p_per_ml_phospho == 0:
            raise ValueError("リン酸NaのP濃度が0です。")
        p_volume = total_p / p_per_ml_phospho  # mL
        calculation_steps += f"\n13. **リン酸NaからのP濃度**: {p_per_ml_phospho} mmol/mL\n"
        calculation_steps += f"    **必要P量**: {total_p:.2f} mmol/day ÷ {p_per_ml_phospho} mmol/mL = **{p_volume:.2f} mL**\n"

        # 総液量の計算
        calculated_total_volume = glucose_volume + amino_acid_volume + phospho_na_volume + kcl_volume + p_volume
        calculation_steps += f"\n14. **計算された総液量**: {glucose_volume:.2f} + {amino_acid_volume:.2f} + {phospho_na_volume:.2f} + {kcl_volume:.2f} + {p_volume:.2f} = **{calculated_total_volume:.2f} mL**\n"
        water_volume = twi - calculated_total_volume  # mL
        calculation_steps += f"    **必要水量**: {twi:.2f} mL/day - {calculated_total_volume:.2f} mL/day = **{water_volume:.2f} mL/day**\n"

        # 蒸留水の量は水量が負になる場合は0にする
        final_water_volume = max(water_volume, 0)
        if water_volume < 0:
            calculation_steps += f"\n15. **警告**: 総液量がTWIを超過しています。製剤の配合を見直してください。\n"
            raise ValueError("総液量がTWIを超過しています。製剤の配合を見直してください。")
        calculation_steps += f"    **蒸留水の量**: max({water_volume:.2f}, 0) = **{final_water_volume:.2f} mL/day**\n"

        # 配合量の詳細を保存
        detailed_mix = {
            "ソルデム3AG": glucose_volume,
            "プレアミンP": amino_acid_volume,
            "リン酸Na": p_volume,
            "KCl": kcl_volume,
            "蒸留水": final_water_volume
        }
        calculation_steps += f"\n16. **配合量の詳細**: {detailed_mix}\n"

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