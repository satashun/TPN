# app.py

import streamlit as st
import pandas as pd
from pydantic import ValidationError
import logging
from models.patient import Patient
from models.solution import Solution
from models.additive import Additive
from models.infusion_mix import InfusionMix
from utils.data_loader import load_solutions, load_additives
from utils.logging_config import setup_logging
from calculation.infusion_calculator import calculate_infusion

setup_logging()
logging.info("アプリケーションの起動")

st.set_page_config(
    page_title="Neonatal TPN 配合計算",
    layout="wide",
    initial_sidebar_state="expanded",
)

def initialize_session_state():
    defaults = {
        'gir_checkbox': True,
        'gir_input': 7.0,
        'amino_acid_checkbox': True,
        'amino_acid_input': 3.0,
        'na_checkbox': True,
        'na_input': 2.5,
        'k_checkbox': True,
        'k_input': 1.5,
        'cl_checkbox': True,
        'cl_input': 0.0,
        'ca_checkbox': True,
        'ca_input': 0.0,
        'mg_checkbox': True,
        'mg_input': 0.0,
        'zn_checkbox': True,
        'zn_input': 0.0,
        'weight': 1.30,
        'twi': 110.0,
        'selected_solution': None,
        'patient': None,
        'infusion_mix': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_values():
    keys_to_keep = {
        'gir_checkbox', 'gir_input', 'amino_acid_checkbox', 'amino_acid_input',
        'na_checkbox', 'na_input', 'k_checkbox', 'k_input', 'cl_checkbox', 'cl_input',
        'ca_checkbox', 'ca_input', 'mg_checkbox', 'mg_input', 'zn_checkbox', 'zn_input',
        'weight', 'twi', 'selected_solution'
    }
    for k in list(st.session_state.keys()):
        if k not in keys_to_keep:
            del st.session_state[k]
    initialize_session_state()
    st.experimental_rerun()

def create_patient_object():
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
        p=None,
        p_included=False,
        fat=None,
        fat_included=False,
        ca=st.session_state.ca_input if st.session_state.ca_checkbox else None,
        ca_included=st.session_state.ca_checkbox,
        mg=st.session_state.mg_input if st.session_state.mg_checkbox else None,
        mg_included=st.session_state.mg_checkbox,
        zn=st.session_state.zn_input if st.session_state.zn_checkbox else None,
        zn_included=st.session_state.zn_checkbox,
        cl=st.session_state.cl_input if st.session_state.cl_checkbox else None,
        cl_included=st.session_state.cl_checkbox
    )

def show_metric(label, input_val, unit, result_val):
    if input_val is not None and result_val is not None:
        diff = result_val - input_val
        # 色分け: 差分が正なら青、負なら赤、ゼロなら緑
        if diff > 0:
            color = "blue"
            status = "過剰"
        elif diff < 0:
            color = "red"
            status = "不足"
        else:
            color = "green"
            status = "適正"
        st.metric(label, f"{result_val:.2f} {unit}", f"{diff:+.2f} ({status})")

def main():
    initialize_session_state()
    
    st.title("Neonatal TPN 配合計算ツール")
    st.markdown("""
    新生児向けTPN配合を計算するツールです。  
    目標値（GIR, アミノ酸量、電解質など）を入力し、「配合を計算」を押すと、  
    実際の配合量を算出します。
    
    **注意：**  
    このツールは参考用で、実際の臨床判断は専門家の裁量で行ってください。
    """)
    
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
        sol = st.session_state.selected_solution
        sol_df = pd.DataFrame({
            "項目": [
                f"ブドウ糖({sol.glucose_unit})", f"Na⁺({sol.na_unit})", f"K⁺({sol.k_unit})",
                f"Cl⁻({sol.cl_unit})", f"P({sol.p_unit})", f"カロリー({sol.calories_unit})",
                f"Mg²⁺({sol.mg_unit})", f"Ca²⁺({sol.ca_unit})", f"Zn({sol.zn_unit})"
            ],
            "値": [
                f"{sol.glucose_percentage}", f"{sol.na}", f"{sol.k}",
                f"{sol.cl}", f"{sol.p}", f"{sol.calories}",
                f"{sol.mg}", f"{sol.ca}", f"{sol.zn}"
            ]
        })
        st.table(sol_df)

    st.markdown("---")
    st.header("患者情報・目標値入力")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本設定")
        weight = st.number_input("体重 (kg)", min_value=0.1, max_value=150.0, step=0.01, key="weight")
        twi = st.number_input("TWI (mL/kg/day)", min_value=50.0, max_value=200.0, step=1.0, key="twi")
        gir_included = st.checkbox("GIR条件", key="gir_checkbox")
        if gir_included:
            gir = st.number_input("GIR (mg/kg/min)", min_value=4.0, max_value=10.0, step=0.1, key="gir_input")
        amino_acid_included = st.checkbox("アミノ酸条件", key="amino_acid_checkbox")
        if amino_acid_included:
            amino_acid = st.number_input("アミノ酸量 (g/kg/day)", min_value=2.0, max_value=4.0, step=0.1, key="amino_acid_input")
    
    with col2:
        st.subheader("電解質等条件")
        na_included = st.checkbox("Na条件", key="na_checkbox")
        if na_included:
            na = st.number_input("Na量 (mEq/kg/day)", min_value=2.0, max_value=4.0, step=0.1, key="na_input")
        k_included = st.checkbox("K条件", key="k_checkbox")
        if k_included:
            k = st.number_input("K量 (mEq/kg/day)", min_value=1.0, max_value=3.0, step=0.1, key="k_input")
        cl_included = st.checkbox("Cl条件", key="cl_checkbox")
        if cl_included:
            cl = st.number_input("Cl量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="cl_input")
        ca_included = st.checkbox("Ca条件", key="ca_checkbox")
        if ca_included:
            ca = st.number_input("Ca量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="ca_input")
        mg_included = st.checkbox("Mg条件", key="mg_checkbox")
        if mg_included:
            mg = st.number_input("Mg量 (mEq/kg/day)", min_value=0.0, max_value=5.0, step=0.1, key="mg_input")
        zn_included = st.checkbox("Zn条件", key="zn_checkbox")
        if zn_included:
            zn = st.number_input("Zn量 (mmol/kg/day)", min_value=0.0, max_value=10.0, step=0.1, key="zn_input")
    
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
            except ValidationError:
                st.error("入力値にエラーがあります。再確認してください。")
            except Exception as e:
                st.error(f"計算中にエラーが発生しました: {e}")

    # 結果表示
    if st.session_state.infusion_mix and st.session_state.patient:
        infusion_mix = st.session_state.infusion_mix
        patient = st.session_state.patient
        
        st.markdown("---")
        st.header("計算結果")
        
        # 目標と実測を一元的に表示するテーブル作成
        # 項目: [TWI, GIR, アミノ酸, Na, K, Cl, Ca, Mg, Zn]
        # 目標はsession_state、実測はinfusion_mixから取得
        target_vs_actual_data = []
        def add_row(name, target, actual, unit):
            diff = actual - target if (target is not None and actual is not None) else None
            target_str = f"{target:.2f}" if target is not None else "-"
            actual_str = f"{actual:.2f}" if actual is not None else "-"
            if diff is not None:
                if diff > 0:
                    status = "過剰"
                elif diff < 0:
                    status = "不足"
                else:
                    status = "適正"
                diff_str = f"{diff:+.2f} ({status})"
            else:
                diff_str = "-"
            target_vs_actual_data.append([name, target_str, actual_str, diff_str])
        
        # 総液量比較 (TWI vs 実際の総液量)
        total_twi = patient.twi * patient.weight
        total_vol = sum(infusion_mix.detailed_mix.values())
        add_row("TWI (mL/day)", total_twi, total_vol, "mL/day")

        if patient.gir_included:
            add_row("GIR (mg/kg/min)", patient.gir, infusion_mix.gir, "mg/kg/min")
        if patient.amino_acid_included:
            add_row("アミノ酸量 (g/kg/day)", patient.amino_acid, infusion_mix.amino_acid, "g/kg/day")
        if patient.na_included:
            add_row("Na量 (mEq/kg/day)", patient.na, infusion_mix.na, "mEq/kg/day")
        if patient.k_included:
            add_row("K量 (mEq/kg/day)", patient.k, infusion_mix.k, "mEq/kg/day")
        if patient.cl_included:
            add_row("Cl量 (mEq/kg/day)", patient.cl, infusion_mix.cl, "mEq/kg/day")
        if patient.ca_included:
            add_row("Ca量 (mEq/kg/day)", patient.ca, infusion_mix.ca, "mEq/kg/day")
        if patient.mg_included:
            add_row("Mg量 (mEq/kg/day)", patient.mg, infusion_mix.mg, "mEq/kg/day")
        if patient.zn_included:
            add_row("Zn量 (mmol/kg/day)", patient.zn, infusion_mix.zn, "mmol/kg/day")
        
        target_vs_actual_df = pd.DataFrame(target_vs_actual_data, columns=["項目", "目標", "実測", "差分"])
        st.subheader("目標 vs 実測")
        st.table(target_vs_actual_df)
        
        # 配合量の詳細テーブルに成分量を追加
        st.subheader("配合量の詳細 (mL/dayと成分量)")
        
        # 定義済みの成分リスト
        components = ['Na', 'K', 'Cl', 'Ca', 'Mg', 'Zn', 'P', 'Amino Acids', 'Fats', 'Glucose']
        
        # テーブルのヘッダー
        table_headers = ["製剤名", "mL/day"] + [f"{comp}量" for comp in components]
        
        # テーブルのデータ
        table_data = []
        for additive_name, volume in infusion_mix.detailed_mix.items():
            additive = additives.get(additive_name)
            if not additive:
                # 添加剤が定義されていない場合はスキップ
                continue
            row = [additive_name, f"{volume:.2f}"]
            # 各成分の量を計算
            for comp in components:
                if comp == "Amino Acids":
                    conc = getattr(additive, 'amino_acid_concentration', 0.0)
                elif comp == "Fats":
                    conc = getattr(additive, 'fat_concentration', 0.0)
                elif comp == "Glucose":
                    conc = getattr(additive, 'glucose_percentage', 0.0) / 100.0  # % to g/mL
                else:
                    attr = f"{comp.lower()}_concentration"
                    conc = getattr(additive, attr, 0.0)
                amount = volume * conc
                # 単位に応じて表示
                if comp == "Glucose":
                    display_amount = f"{amount:.2f} g/day"
                elif comp == "Amino Acids" or comp == "Fats":
                    display_amount = f"{amount:.2f} g/day"
                elif comp == "Zn":
                    display_amount = f"{amount:.2f} mmol/day"
                elif comp == "P":
                    display_amount = f"{amount:.2f} mmol/day"
                else:
                    display_amount = f"{amount:.2f} mEq/day"
                row.append(display_amount)
            table_data.append(row)
        
        # 合計行を計算
        totals = ["合計", f"{sum(infusion_mix.detailed_mix.values()):.2f}"]
        total_components = {comp: 0.0 for comp in components}
        for additive_name, volume in infusion_mix.detailed_mix.items():
            additive = additives.get(additive_name)
            if not additive:
                continue
            for comp in components:
                if comp == "Amino Acids":
                    conc = getattr(additive, 'amino_acid_concentration', 0.0)
                elif comp == "Fats":
                    conc = getattr(additive, 'fat_concentration', 0.0)
                elif comp == "Glucose":
                    conc = getattr(additive, 'glucose_percentage', 0.0) / 100.0  # % to g/mL
                else:
                    attr = f"{comp.lower()}_concentration"
                    conc = getattr(additive, attr, 0.0)
                amount = volume * conc
                total_components[comp] += amount
        
        # 合計行に各成分の総量を追加
        for comp in components:
            if comp == "Glucose":
                display_amount = f"{total_components[comp]:.2f} g/day"
            elif comp == "Amino Acids" or comp == "Fats":
                display_amount = f"{total_components[comp]:.2f} g/day"
            elif comp == "Zn":
                display_amount = f"{total_components[comp]:.2f} mmol/day"
            elif comp == "P":
                display_amount = f"{total_components[comp]:.2f} mmol/day"
            else:
                display_amount = f"{total_components[comp]:.2f} mEq/day"
            totals.append(display_amount)
        
        table_data.append(totals)
        
        # DataFrameの作成
        infusion_detail_df = pd.DataFrame(table_data, columns=table_headers)
        st.table(infusion_detail_df)
        
        # 折りたたみで計算ステップ詳細
        with st.expander("詳細計算ステップを表示"):
            steps_formatted = infusion_mix.calculation_steps.replace("\n", "\n")
            st.markdown(f"**計算ステップ:**\n\n{steps_formatted}")
            st.info("必要に応じて計算プロセスを参照してください。")
    
if __name__ == "__main__":
    main()
