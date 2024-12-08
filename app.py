# app.py

import streamlit as st
import pandas as pd
from pydantic import ValidationError
import logging
from typing import Dict

from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from utils.data_loader import load_solutions, load_additives
from utils.logging_config import setup_logging
from calculation.infusion_calculator import calculate_infusion

# ログ設定
setup_logging()
logging.info("アプリケーションの起動")

# Streamlitのページ設定
st.set_page_config(
    page_title="Neonatal TPN 配合計算",
    layout="wide",
    initial_sidebar_state="expanded",
)

def initialize_session_state():
    """
    セッションステートの初期化
    """
    defaults = {
        'gir_checkbox': True,
        'gir_input': 7.0,
        'amino_acid_checkbox': False,
        'amino_acid_input': 3.0,
        'na_checkbox': True,
        'na_input': 2.5,
        'k_checkbox': True,
        'k_input': 1.5,
        'cl_checkbox': True,
        'cl_input': 0.0,
        'ca_checkbox': False,
        'ca_input': 0.0,
        'mg_checkbox': False,
        'mg_input': 0.0,
        'zn_checkbox': False,
        'zn_input': 0.0,
        'fat_checkbox': False,
        'fat_input': 0.0,
        'weight': 1.50,
        'twi': 110.0,
        'selected_solution': None,
        'patient': None,
        'infusion_mix': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_values():
    """
    セッションステートのリセット
    """
    keys_to_keep = {
        'gir_checkbox', 'gir_input', 'amino_acid_checkbox', 'amino_acid_input',
        'na_checkbox', 'na_input', 'k_checkbox', 'k_input', 'cl_checkbox', 'cl_input',
        'ca_checkbox', 'ca_input', 'mg_checkbox', 'mg_input', 'zn_checkbox', 'zn_input',
        'fat_checkbox', 'fat_input',
        'weight', 'twi', 'selected_solution'
    }
    for k in list(st.session_state.keys()):
        if k not in keys_to_keep:
            del st.session_state[k]
    initialize_session_state()
    st.experimental_rerun()

def create_patient_object() -> Patient:
    """
    Streamlitの入力からPatientオブジェクトを作成
    """
    return Patient(
        weight=st.session_state.weight,
        twi=st.session_state.twi,
        gir=st.session_state.gir_input if st.session_state.gir_checkbox else None,
        gir_included=st.session_state.gir_checkbox,
        amino_acid=st.session_state.amino_acid_input if st.session_state.amino_acid_checkbox else None,
        amino_acid_included=st.session_state.amino_acid_checkbox,
        na=st.session_state.na_input if st.session_state.na_checkbox else None,
        na_included=st.session_state.na_checkbox,
        k=st.session_state.k_input if st.session_state.k_checkbox else None,
        k_included=st.session_state.k_checkbox,
        p=None,  # pは未使用
        p_included=False,
        fat=st.session_state.fat_input if st.session_state.fat_checkbox else None,
        fat_included=st.session_state.fat_checkbox,
        ca=st.session_state.ca_input if st.session_state.ca_checkbox else None,
        ca_included=st.session_state.ca_checkbox,
        mg=st.session_state.mg_input if st.session_state.mg_checkbox else None,
        mg_included=st.session_state.mg_checkbox,
        zn=st.session_state.zn_input if st.session_state.zn_checkbox else None,
        zn_included=st.session_state.zn_checkbox,
        cl=st.session_state.cl_input if st.session_state.cl_checkbox else None,
        cl_included=st.session_state.cl_checkbox
    )

def display_solution_details(solution: Solution):
    """
    選択されたベース製剤の詳細を表示
    """
    sol_df = pd.DataFrame({
        "項目": [
            f"ブドウ糖({solution.glucose_unit})", f"Na⁺({solution.na_unit})", f"K⁺({solution.k_unit})",
            f"Cl⁻({solution.cl_unit})", f"P({solution.p_unit})", f"カロリー({solution.calories_unit})",
            f"Mg²⁺({solution.mg_unit})", f"Ca²⁺({solution.ca_unit})", f"Zn({solution.zn_unit})",
            f"脂肪({solution.fat_concentration_unit})"  # 脂肪も追加
        ],
        "値": [
            f"{solution.glucose_percentage} %",
            f"{solution.na} {solution.na_unit}",
            f"{solution.k} {solution.k_unit}",
            f"{solution.cl} {solution.cl_unit}",
            f"{solution.p} {solution.p_unit}",
            f"{solution.calories} {solution.calories_unit}",
            f"{solution.mg} {solution.mg_unit}",
            f"{solution.ca} {solution.ca_unit}",
            f"{solution.zn} {solution.zn_unit}",
            f"{solution.fat_concentration} {solution.fat_concentration_unit}"
        ]
    })
    st.table(sol_df)

def display_calculation_results(infusion_mix: InfusionMix, patient: Patient, additives: Dict[str, Additive]):
    """
    計算結果を表示
    """
    st.markdown("---")
    st.header("計算結果")

    # 目標と実測の差分表示
    components_all = [
        ('Glucose', 'g/day'),
        ('Amino Acids', 'g/day'),
        ('Na', 'mEq/day'),
        ('K', 'mEq/day'),
        ('Cl', 'mEq/day'),
        ('Ca', 'mEq/day'),
        ('Mg', 'mEq/day'),
        ('Zn', 'mmol/day'),
        ('P', 'mmol/day'),
        ('Fats', 'g/day')
    ]

    target_actual_data = []
    for comp_name, unit in components_all:
        target = infusion_mix.input_amounts.get(comp_name, 0.0)
        actual = infusion_mix.nutrient_totals.get(comp_name, 0.0)
        if target > 0:
            ratio = actual / target
            difference = (ratio - 1) * 100  # パーセンテージ
            if abs(difference) <= 10:
                status = "適正"
            elif abs(difference) <= 20:
                status = "やや適正"
            elif abs(difference) <= 30:
                status = "注意"
            else:
                status = "要確認"
            diff_str = f"{difference:+.2f}% ({status})"
        else:
            if actual == 0:
                diff_str = "-"
            else:
                diff_str = "目標未設定"
        target_str = f"{target:.2f} {unit}" if target > 0 else "-"
        actual_str = f"{actual:.2f} {unit}" if actual > 0 else "-"
        target_actual_data.append([comp_name, target_str, actual_str, diff_str])

    # 全成分表示
    st.subheader("目標 vs 実測 (全成分)")
    target_vs_actual_df = pd.DataFrame(target_actual_data, columns=["項目", "目標", "実測", "差分"])
    st.table(target_vs_actual_df)

    # 配合量の詳細テーブル
    st.subheader("配合量の詳細 (mL/dayと成分量)")

    components = ['Na', 'K', 'Cl', 'Ca', 'Mg', 'Zn', 'P', 'Amino Acids', 'Fats', 'Glucose']
    table_headers = ["製剤名", "mL/day"] + components

    table_data = []
    total_components_dict = {c:0.0 for c in components}

    # 製剤名と使用量から栄養素供給量を計算
    for additive_name, vol in infusion_mix.detailed_mix.items():
        row = [additive_name, f"{vol:.2f}"]
        # 栄養素の供給量を計算
        if additive_name.startswith("ベース製剤"):
            # ベース製剤の栄養素供給量を取得
            sol = infusion_mix.detailed_mix.get(additive_name)
            # 栄養素の貢献度を計算
            contributions = {}
            base_sol = infusion_mix.detailed_mix.get(additive_name)
            # ベース製剤の場合、infusion_calculator.pyで計算された nutrient_totals に基づく
            for c in components:
                contributions[c] = infusion_mix.nutrient_totals.get(c, 0.0)
                total_components_dict[c] += contributions[c]
                row.append(f"{contributions[c]:.2f}")
        else:
            # 添加剤の場合
            additive = additives.get(additive_name)
            if additive:
                na = additive.na_concentration * vol
                k = additive.k_concentration * vol
                cl = additive.cl_concentration * vol
                ca = additive.ca_concentration * vol
                mg = additive.mg_concentration * vol
                zn = additive.zn_concentration * vol
                p = additive.p_concentration * vol
                amino = additive.amino_acid_concentration * vol
                fat = additive.fat_concentration * vol
                glucose = 0.0  # 添加剤には含まれないと仮定
            else:
                na = k = cl = ca = mg = zn = p = amino = fat = glucose = 0.0

            contributions = {
                'Na': na,
                'K': k,
                'Cl': cl,
                'Ca': ca,
                'Mg': mg,
                'Zn': zn,
                'P': p,
                'Amino Acids': amino,
                'Fats': fat,
                'Glucose': glucose
            }

            for c in components:
                val = contributions.get(c, 0.0)
                row.append(f"{val:.2f}")
                total_components_dict[c] += val

        table_data.append(row)

    # 合計行
    totals = ["合計", f"{sum(infusion_mix.detailed_mix.values()):.2f}"]
    for c in components:
        totals.append(f"{total_components_dict[c]:.2f}")
    table_data.append(totals)

    infusion_detail_df = pd.DataFrame(table_data, columns=table_headers)
    st.dataframe(infusion_detail_df.style.set_properties(**{'text-align': 'left'}))

    # 計算ステップの表示
    with st.expander("詳細計算ステップを表示"):
        st.markdown(f"**計算ステップ:**\n\n{infusion_mix.calculation_steps}")

def main():
    initialize_session_state()
    
    st.title("Neonatal TPN 配合計算ツール")
    st.markdown("---")
    st.header("ベース製剤選択")

    solutions = load_solutions()
    additives = load_additives()

    if not solutions or not additives:
        st.error("データロード失敗。ファイルを確認してください。")
        st.stop()

    selected_solution_name = st.selectbox(
        "ベース製剤を選択",
        [sol.name for sol in solutions],
        key="base_solution_selectbox"
    )
    st.session_state.selected_solution = next((sol for sol in solutions if sol.name == selected_solution_name), None)

    if st.session_state.selected_solution:
        display_solution_details(st.session_state.selected_solution)

    st.markdown("---")
    st.header("患者情報・目標値入力")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本設定")
        st.number_input("体重 (kg)", min_value=0.1, max_value=150.0, step=0.01, key="weight")
        st.number_input("TWI (mL/kg/day)", min_value=50.0, max_value=200.0, step=1.0, key="twi")
        gir_included = st.checkbox("GIR条件", key="gir_checkbox")
        if gir_included:
            st.number_input("GIR (mg/kg/min)", min_value=4.0, max_value=10.0, step=0.1, key="gir_input")
        amino_acid_included = st.checkbox("アミノ酸条件", key="amino_acid_checkbox", value=False)
        if amino_acid_included:
            st.number_input("アミノ酸量 (g/kg/day)", min_value=2.0, max_value=4.0, step=0.1, key="amino_acid_input")
        fat_included = st.checkbox("脂肪条件", key="fat_checkbox")
        if fat_included:
            st.number_input("脂肪量 (g/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="fat_input")

    with col2:
        st.subheader("電解質等条件")
        na_included = st.checkbox("Na条件", key="na_checkbox")
        if na_included:
            st.number_input("Na量 (mEq/kg/day)", min_value=2.0, max_value=4.0, step=0.1, key="na_input")
        k_included = st.checkbox("K条件", key="k_checkbox")
        if k_included:
            st.number_input("K量 (mEq/kg/day)", min_value=1.0, max_value=3.0, step=0.1, key="k_input")
        cl_included = st.checkbox("Cl条件", key="cl_checkbox")
        if cl_included:
            st.number_input("Cl量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="cl_input")
        ca_included = st.checkbox("Ca条件", value=False, key="ca_checkbox")
        if ca_included:
            st.number_input("Ca量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="ca_input")
        mg_included = st.checkbox("Mg条件", value=False, key="mg_checkbox")
        if mg_included:
            st.number_input("Mg量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="mg_input")
        zn_included = st.checkbox("Zn条件", value=False, key="zn_checkbox")
        if zn_included:
            st.number_input("Zn量 (mmol/kg/day)", min_value=0.0, max_value=10.0, step=0.1, key="zn_input")

    st.markdown("---")
    button_cols = st.columns([1, 1, 4])
    with button_cols[0]:
        if st.button('リセット', type="secondary"):
            reset_values()
    with button_cols[1]:
        calc_button = st.button("配合を計算", type="primary")
    
    if calc_button:
        with st.spinner("計算中..."):
            try:
                if st.session_state.selected_solution is None:
                    st.error("ベース製剤を選択してください。")
                    raise ValueError("selected_solution is None")
                patient = create_patient_object()
                st.session_state.patient = patient
                infusion_mix = calculate_infusion(patient, st.session_state.selected_solution, additives)
                st.session_state.infusion_mix = infusion_mix
            except ValidationError as ve:
                st.error("入力値にエラーがあります。再確認してください。")
                logging.error(f"ValidationError: {ve}")
            except ValueError as ve:
                st.error(str(ve))
                logging.error(f"ValueError: {ve}")
            except Exception as e:
                st.error(f"計算中にエラーが発生しました: {e}")
                logging.error(f"Exception: {e}")

    if 'infusion_mix' in st.session_state and st.session_state['infusion_mix'] is not None:
        infusion_mix = st.session_state['infusion_mix']
        patient = st.session_state['patient']
        display_calculation_results(infusion_mix, patient, additives)

if __name__ == "__main__":
    main()
