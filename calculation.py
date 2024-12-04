# calculation.py
from models import Patient, Solution, InfusionMix
import logging

def calculate_infusion(patient: Patient, solution: Solution) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択された製剤: {solution}")
        
        weight = patient.weight
        twi = patient.twi * weight  # 総投与量 (mL/day)
        gir = patient.gir  # mg/kg/min
        amino_acid = patient.amino_acid  # g/kg/day
        na = patient.na  # mEq/kg/day
        k = patient.k  # mEq/kg/day
        p = patient.p  # mmol/kg/day
        
        # 必要量の計算
        total_gir = gir * weight * 60 * 24 / 1000  # g/day
        total_amino_acid = amino_acid * weight  # g/day
        total_na = na * weight  # mEq/day
        total_k = k * weight  # mEq/day
        total_p = p * weight  # mmol/day
        
        logging.debug(f"必要GIR: {total_gir} g/day")
        logging.debug(f"必要アミノ酸: {total_amino_acid} g/day")
        logging.debug(f"必要Na: {total_na} mEq/day")
        logging.debug(f"必要K: {total_k} mEq/day")
        logging.debug(f"必要P: {total_p} mmol/day")
        
        # ブドウ糖の計算
        glucose_per_ml = solution.glucose_percentage / 100.0  # g/mL
        if glucose_per_ml == 0:
            raise ValueError("選択された製剤のブドウ糖濃度が0です。")
        glucose_volume = total_gir / glucose_per_ml  # mL
        logging.debug(f"ブドウ糖濃度: {solution.glucose_percentage}%, 必要ブドウ糖量: {glucose_volume} mL")
        
        # アミノ酸の計算
        # プレアミンPのアミノ酸濃度は7600mg/100mL = 76 mg/mL
        amino_acid_concentration = 76.0 / 1000.0  # g/mL
        if amino_acid_concentration == 0:
            raise ValueError("プレアミンPのアミノ酸濃度が0です。")
        amino_acid_volume = total_amino_acid / amino_acid_concentration  # mL
        logging.debug(f"アミノ酸濃度: {amino_acid_concentration} g/mL, 必要アミノ酸量: {amino_acid_volume} mL")
        
        # Na量の計算
        base_na_total = (solution.na * glucose_volume) / 1000.0  # mEq/day
        additional_na = total_na - base_na_total  # mEq/day
        logging.debug(f"ベース製剤からのNa: {base_na_total} mEq/day, 追加で必要なNa: {additional_na} mEq/day")
        
        # リン酸NaからのNa
        # リン酸Na: 20mL中P 10mmol、Na 15mEq => Na 0.75 mEq/mL
        na_per_ml_phospho = 15.0 / 20.0  # mEq/mL
        if na_per_ml_phospho == 0:
            raise ValueError("リン酸NaのNa濃度が0です。")
        phospho_na_volume = additional_na / na_per_ml_phospho  # mL
        logging.debug(f"リン酸NaからのNa濃度: {na_per_ml_phospho} mEq/mL, 必要Na量: {phospho_na_volume} mL")
        
        # K量の計算
        base_k_total = (solution.k * glucose_volume) / 1000.0  # mEq/day
        additional_k = total_k - base_k_total  # mEq/day
        logging.debug(f"ベース製剤からのK: {base_k_total} mEq/day, 追加で必要なK: {additional_k} mEq/day")
        
        # KClからのK
        # KCl: K 1 mEq/mL
        kcl_k_concentration = 1.0  # mEq/mL
        if kcl_k_concentration == 0:
            raise ValueError("KClのK濃度が0です。")
        kcl_volume = additional_k / kcl_k_concentration  # mL
        logging.debug(f"KClからのK濃度: {kcl_k_concentration} mEq/mL, 必要K量: {kcl_volume} mL")
        
        # P量の計算
        # リン酸Na: P 10mmol/20mL = 0.5 mmol/mL
        p_per_ml_phospho = 10.0 / 20.0  # mmol/mL
        if p_per_ml_phospho == 0:
            raise ValueError("リン酸NaのP濃度が0です。")
        p_volume = total_p / p_per_ml_phospho  # mL
        logging.debug(f"リン酸NaからのP濃度: {p_per_ml_phospho} mmol/mL, 必要P量: {p_volume} mL")
        
        # 総液量の計算
        calculated_total_volume = glucose_volume + amino_acid_volume + phospho_na_volume + kcl_volume + p_volume
        water_volume = twi - calculated_total_volume  # mL
        logging.debug(f"計算された総液量: {calculated_total_volume} mL")
        logging.debug(f"必要水量: {water_volume} mL")
        
        # 蒸留水の量は水量が負になる場合は0にする
        final_water_volume = max(water_volume, 0)
        if water_volume < 0:
            logging.warning("総液量がTWIを超過しています。製剤の配合を見直してください。")
            raise ValueError("総液量がTWIを超過しています。製剤の配合を見直してください。")
        logging.debug(f"蒸留水の量: {final_water_volume} mL")
        
        # 配合量の詳細を保存
        detailed_mix = {
            "ソルデム3AG": glucose_volume,
            "プレアミンP": amino_acid_volume,
            "リン酸Na": p_volume,
            "KCl": kcl_volume,
            "蒸留水": final_water_volume
        }
        logging.debug(f"配合量の詳細: {detailed_mix}")
        
        # 計算結果の作成
        infusion_mix = InfusionMix(
            gir=gir,
            amino_acid=amino_acid,
            na=na,
            k=k,
            p=p,
            detailed_mix=detailed_mix
        )
        
        logging.info("計算完了")
        return infusion_mix
    
    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
