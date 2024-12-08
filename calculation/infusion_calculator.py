# calculation/infusion_calculator.py

from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from typing import Dict
import logging
import pulp

def get_nutrient_contribution(nutrient: str, solution: Solution) -> float:
    """
    製剤から特定の栄養素への貢献度を返す。
    単位はg/day, mEq/day, mmol/dayなどで統一。
    """
    mapping = {
        'Glucose': solution.glucose_percentage / 100.0,  # g/mL
        'Na': solution.na / 1000.0,                      # mEq/mL
        'K': solution.k / 1000.0,                        # mEq/mL
        'Cl': solution.cl / 1000.0,                      # mEq/mL
        'Ca': solution.ca / 1000.0,                      # mEq/mL
        'Mg': solution.mg / 1000.0,                      # mEq/mL
        'Zn': solution.zn / 1000.0,                      # mmol/mL
        'P': solution.p / 1000.0,                        # mmol/mL
        'Amino Acids': 0.0,                              # ベース製剤には含まれないと仮定
        'Fats': 0.0                                       # ベース製剤には含まれないと仮定
    }
    return mapping.get(nutrient, 0.0)

def get_additive_nutrient_contribution(nutrient: str, additive: Additive) -> float:
    """
    添加剤から特定の栄養素への貢献度を返す。
    単位はg/day, mEq/day, mmol/dayなどで統一。
    """
    mapping = {
        'Glucose': 0.0,  # 添加剤には含まれないと仮定
        'Na': additive.na_concentration,          # mEq/mL
        'K': additive.k_concentration,            # mEq/mL
        'Cl': additive.cl_concentration,          # mEq/mL
        'Ca': additive.ca_concentration,          # mEq/mL
        'Mg': additive.mg_concentration,          # mEq/mL
        'Zn': additive.zn_concentration,          # mmol/mL
        'P': additive.p_concentration,            # mmol/mL
        'Amino Acids': additive.amino_acid_concentration,  # g/mL
        'Fats': additive.fat_concentration         # g/mL
    }
    return mapping.get(nutrient, 0.0)

def get_nutrient_unit(nutrient: str) -> str:
    """
    栄養素の単位を返す。
    """
    units = {
        'Glucose': 'g/day',
        'Amino Acids': 'g/day',
        'Na': 'mEq/day',
        'K': 'mEq/day',
        'Cl': 'mEq/day',
        'Ca': 'mEq/day',
        'Mg': 'mEq/day',
        'Zn': 'mmol/day',
        'P': 'mmol/day',
        'Fats': 'g/day'
    }
    return units.get(nutrient, '')

def calculate_infusion(patient: Patient, base_solution: Solution, additives: Dict[str, Additive]) -> InfusionMix:
    try:
        logging.info("計算開始")
        logging.debug(f"患者データ: {patient}")
        logging.debug(f"選択されたベース製剤: {base_solution}")
        logging.debug(f"選択された添加剤: {additives}")

        # 目標栄養素の設定
        targets = {
            'Glucose': 0.0,  # GIRから計算後に設定
            'Amino Acids': patient.amino_acid * patient.weight if patient.amino_acid_included and patient.amino_acid else 0.0,  # g/day
            'Na': patient.na * patient.weight if patient.na_included and patient.na else 0.0,  # mEq/day
            'K': patient.k * patient.weight if patient.k_included and patient.k else 0.0,  # mEq/day
            'Cl': patient.cl * patient.weight if patient.cl_included and patient.cl else 0.0,  # mEq/day
            'Ca': patient.ca * patient.weight if patient.ca_included and patient.ca else 0.0,  # mEq/day
            'Mg': patient.mg * patient.weight if patient.mg_included and patient.mg else 0.0,  # mEq/day
            'Zn': patient.zn * patient.weight if patient.zn_included and patient.zn else 0.0,  # mmol/day
            'P': 0.0,  # 未使用
            'Fats': patient.fat * patient.weight if patient.fat_included and patient.fat else 0.0  # g/day
        }

        # GIRからGlucoseの目標を計算
        if patient.gir_included and patient.gir:
            # GIR (mg/kg/min) × 1440 min/day = mg/kg/day
            # mg/kg/day × kg = mg/day → g/day
            targets['Glucose'] = (patient.gir * patient.weight * 1440) / 1000.0  # g/day

        logging.debug(f"目標栄養素: {targets}")

        # 使用可能な製剤のリスト（ベース製剤と添加剤）
        available_solutions = {f"ベース製剤（{base_solution.name}）": base_solution}
        available_solutions.update(additives)

        # PuLPの最適化問題を定義
        prob = pulp.LpProblem("TPN_Infusion_Optimization", pulp.LpMinimize)

        # 各製剤の使用量（mL/day）の変数を定義
        solution_vars = {name: pulp.LpVariable(name, lowBound=0, cat='Continuous') for name in available_solutions}

        # 目的関数: 総投与量の最小化
        prob += pulp.lpSum([var for var in solution_vars.values()]), "Total_Infusion_Volume"

        # 栄養素の供給量制約
        nutrients = ['Glucose', 'Amino Acids', 'Na', 'K', 'Cl', 'Ca', 'Mg', 'Zn', 'P', 'Fats']

        for nutrient in nutrients:
            if targets.get(nutrient, 0.0) > 0:
                # 各栄養素の供給量を計算
                supply = []
                for sol_name, sol in available_solutions.items():
                    if sol_name.startswith("ベース製剤"):
                        supply.append(get_nutrient_contribution(nutrient, sol) * solution_vars[sol_name])
                    else:
                        additive = additives.get(sol_name)
                        if additive:
                            supply.append(get_additive_nutrient_contribution(nutrient, additive) * solution_vars[sol_name])
                # 目標値の90%〜110%を満たすように制約
                prob += pulp.lpSum(supply) >= 0.9 * targets[nutrient], f"{nutrient}_lower_bound"
                prob += pulp.lpSum(supply) <= 1.1 * targets[nutrient], f"{nutrient}_upper_bound"

        # 最適化を実行
        prob_status = prob.solve()

        logging.debug(f"PuLPのステータス: {pulp.LpStatus[prob.status]}")

        if pulp.LpStatus[prob.status] != 'Optimal':
            # 最適解が見つからない場合
            logging.error("最適化問題が解けませんでした。入力値を見直してください。")
            raise ValueError("最適化問題が解けませんでした。入力値を見直してください。")

        # 結果の取得
        detailed_mix = {name: solution_vars[name].varValue for name in solution_vars}
        logging.debug(f"詳細配合量: {detailed_mix}")

        # 栄養素の総供給量を計算
        nutrient_totals = {}
        for nutrient in nutrients:
            total = 0.0
            for sol_name, sol in available_solutions.items():
                if sol_name.startswith("ベース製剤"):
                    contribution = get_nutrient_contribution(nutrient, sol) * detailed_mix[sol_name]
                else:
                    additive = additives.get(sol_name)
                    if additive:
                        contribution = get_additive_nutrient_contribution(nutrient, additive) * detailed_mix[sol_name]
                    else:
                        contribution = 0.0
                total += contribution
            nutrient_totals[nutrient] = total

        logging.debug(f"栄養素の総供給量: {nutrient_totals}")

        # 差分の計算
        differences = {}
        for nutrient in nutrients:
            target = targets.get(nutrient, 0.0)
            actual = nutrient_totals.get(nutrient, 0.0)
            if target > 0:
                ratio = actual / target
                difference = (ratio - 1) * 100  # パーセンテージ
                differences[nutrient] = difference
            else:
                differences[nutrient] = 0.0  # 未使用

        logging.debug(f"差分（%）: {differences}")

        # 差分が200%以上かチェック
        for nutrient, diff in differences.items():
            if abs(diff) >= 200:
                logging.error(f"{nutrient} の供給量が目標と200%以上異なります。目標: {targets[nutrient]}, 実測: {actual}")
                raise ValueError(f"{nutrient} の供給量が目標と200%以上異なります。数値を見直してください。")

        # 差分が10%以内かどうかチェック
        within_10 = all(abs(diff) <= 10 for nutrient, diff in differences.items() if targets.get(nutrient, 0.0) > 0)
        status_message = ""
        if within_10:
            status_message = "目標値と実測値の差が10%以内に収まりました。"
            logging.info(status_message)
        else:
            # 10%を超えている栄養素を抽出
            over_10 = {n: d for n, d in differences.items() if targets.get(n, 0.0) > 0 and abs(d) > 10 and abs(d) <= 30}
            if over_10:
                status_message = "一部の栄養素が10%を超えていますが、30%以内に収まっています。注意してご確認ください。"
                logging.warning(status_message)
            else:
                # 10%も30%も超えている栄養素がある場合
                status_message = "一部の栄養素が30%を超えています。数値を見直してください。"
                logging.warning(status_message)

        # 計算ステップの記録
        calculation_steps = "### 計算ステップ\n"
        calculation_steps += "1. **目標栄養素の設定**\n"
        for nutrient, target in targets.items():
            calculation_steps += f"   - {nutrient}: {target:.2f} {get_nutrient_unit(nutrient)}\n"
        calculation_steps += "2. **最適化モデルの構築**\n"
        calculation_steps += "   - 製剤の使用量を変数として定義。\n"
        calculation_steps += "   - 目的関数: 総投与量の最小化。\n"
        calculation_steps += "   - 栄養素の供給量が目標の±10%を満たすよう制約を設定。\n"
        calculation_steps += "3. **最適化の実行**\n"
        calculation_steps += f"   - 総投与量: {sum(detailed_mix.values()):.2f} mL/day\n"
        calculation_steps += f"   - {status_message}\n"

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
                'Glucose': 'g/day',
                'Amino Acids': 'g/day',
                'Na': 'mEq/day',
                'K': 'mEq/day',
                'Cl': 'mEq/day',
                'Ca': 'mEq/day',
                'Mg': 'mEq/day',
                'Zn': 'mmol/day',
                'P': 'mmol/day',
                'Fats': 'g/day'
            },
            input_amounts=targets,
            input_units={
                'Glucose': 'g/day',
                'Amino Acids': 'g/day',
                'Na': 'mEq/day',
                'K': 'mEq/day',
                'Cl': 'mEq/day',
                'Ca': 'mEq/day',
                'Mg': 'mEq/day',
                'Zn': 'mmol/day',
                'P': 'mmol/day',
                'Fats': 'g/day'
            }
        )

        logging.info("計算完了")
        return infusion_mix

    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        raise ve
    except Exception as e:
        logging.error(f"計算中にエラーが発生しました: {e}")
        raise e
