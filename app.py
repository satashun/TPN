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

# ログ設定
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
        'amino_acid_checkbox': False, # デフォルトOFF
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
        p=None, # pは特に要求されていない場合None
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
            except ValidationError:
                st.error("入力値にエラーがあります。再確認してください。")
            except Exception as e:
                st.error(f"計算中にエラーが発生しました: {e}")

    if 'infusion_mix' in st.session_state and st.session_state['infusion_mix'] is not None:
        infusion_mix = st.session_state['infusion_mix']
        patient = st.session_state['patient']
        
        st.markdown("---")
        st.header("計算結果")

        # 全成分表示用
        components_all = [
            ('GIR','mg/kg/min'),
            ('Amino Acids','g/kg/day'),
            ('Na','mEq/kg/day'),
            ('K','mEq/kg/day'),
            ('Cl','mEq/kg/day'),
            ('Ca','mEq/kg/day'),
            ('Mg','mEq/kg/day'),
            ('Zn','mmol/kg/day'),
            ('P','mmol/kg/day'),
            ('Fats','g/kg/day'),
            ('Glucose','g/kg/day')
        ]

        # nutrient_totalsはtotal/day単位(g/day,mEq/day,etc.)で格納されている
        # units for nutrient_totals:
        # GIR: g/day
        # Amino Acids, Fats, Glucose: g/day
        # Na, K, Cl, Ca, Mg: mEq/day
        # Zn, P: mmol/day

        # ターゲットと実測の取得関数
        def get_target(comp_name):
            if comp_name == 'GIR':
                return patient.gir if patient.gir_included else None
            elif comp_name == 'Amino Acids':
                return patient.amino_acid if patient.amino_acid_included else None
            elif comp_name == 'Na':
                return patient.na if patient.na_included else None
            elif comp_name == 'K':
                return patient.k if patient.k_included else None
            elif comp_name == 'Cl':
                return patient.cl if patient.cl_included else None
            elif comp_name == 'Ca':
                return patient.ca if patient.ca_included else None
            elif comp_name == 'Mg':
                return patient.mg if patient.mg_included else None
            elif comp_name == 'Zn':
                return patient.zn if patient.zn_included else None
            elif comp_name == 'P':
                return None  # pは未設定
            elif comp_name == 'Fats':
                return patient.fat if patient.fat_included else None
            elif comp_name == 'Glucose':
                return None  # Glucoseの目標は別途設定しない
            else:
                return None

        def get_units_for_total(comp_name):
            if comp_name == 'GIR':
                return 'g/day'
            elif comp_name in ['Amino Acids','Fats','Glucose']:
                return 'g/day'
            elif comp_name in ['Na','K','Cl','Ca','Mg']:
                return 'mEq/day'
            elif comp_name in ['Zn','P']:
                return 'mmol/day'
            else:
                return ''

        def get_actual_values(comp_name):
            if comp_name == 'GIR':
                # infusion_mix.gir は g/day である
                return (infusion_mix.gir, infusion_mix.nutrient_totals.get('GIR', 0.0))
            else:
                a_total = infusion_mix.nutrient_totals.get(comp_name, 0.0)
                a_perkg = a_total / patient.weight
                return (a_perkg, a_total)

        # 差分計算とデータ整理
        target_actual_data = []

        for comp_name, unit in components_all:
            t = get_target(comp_name)
            a_perkg, a_total = get_actual_values(comp_name)
            diff_str = "-"
            if t is not None and a_perkg is not None:
                if comp_name == 'GIR':
                    diff = infusion_mix.gir - t  # g/day単位ではなく元の単位で差分を計算
                else:
                    diff = a_perkg - t
                if diff > 0:
                    status = "過剰"
                elif diff < 0:
                    status = "不足"
                else:
                    status = "適正"
                diff_str = f"{diff:+.2f} ({status})"
            target_str = f"{t:.2f} {unit}" if t is not None else "-"
            actual_str = f"{a_perkg:.2f} {unit}" if a_perkg is not None else "-"
            actual_total_str = f"{a_total:.2f} {get_units_for_total(comp_name)}" if a_total is not None else "-"
            target_actual_data.append([comp_name, target_str, actual_str, actual_total_str, diff_str])

        # 全成分表示
        st.subheader("目標 vs 実測 (全成分)")
        target_vs_actual_df = pd.DataFrame(target_actual_data, columns=["項目", "目標", "実測 (×/kg/day または mg/kg/min)", "実測 (total/day)", "差分"])
        st.table(target_vs_actual_df)

        # 配合量の詳細テーブル
        st.subheader("配合量の詳細 (mL/dayと成分量)")

        components = ['Na', 'K', 'Cl', 'Ca', 'Mg', 'Zn', 'P', 'Amino Acids', 'Fats', 'Glucose']
        table_headers = ["製剤名", "mL/day"] + components

        def conv(value, unit, volume):
            if "/L" in unit:
                return value * (volume / 1000.0)  # g/L * L = g
            elif "/mL" in unit:
                return value * volume  # g/mL * mL = g
            else:
                return value * (volume / 1000.0)  # デフォルトは /L と同様

        def get_solution_nutrients(solution:Solution, volume:float):
            na = conv(solution.na, solution.na_unit, volume)
            k = conv(solution.k, solution.k_unit, volume)
            cl = conv(solution.cl, solution.cl_unit, volume)
            p = conv(solution.p, solution.p_unit, volume)
            mg = conv(solution.mg, solution.mg_unit, volume)
            ca = conv(solution.ca, solution.ca_unit, volume)
            zn = conv(solution.zn, solution.zn_unit, volume)
            glc = conv(solution.glucose_percentage, solution.glucose_unit, volume)
            fat = 0.0
            amino = 0.0
            return {'Na':na, 'K':k, 'Cl':cl, 'Ca':ca, 'Mg':mg, 'Zn':zn, 'P':p, 'Amino Acids':amino,'Fats':fat,'Glucose':glc}

        def get_additive_nutrients(add:Additive, volume:float):
            na = conv(add.na_concentration, add.na_concentration_unit, volume)
            k = conv(add.k_concentration, add.k_concentration_unit, volume)
            cl = conv(add.cl_concentration, add.cl_concentration_unit, volume)
            ca = conv(add.ca_concentration, add.ca_concentration_unit, volume)
            mg = conv(add.mg_concentration, add.mg_concentration_unit, volume)
            zn = conv(add.zn_concentration, add.zn_concentration_unit, volume)
            p = conv(add.p_concentration, add.p_concentration_unit, volume)
            amino = conv(add.amino_acid_concentration, add.amino_acid_concentration_unit, volume)
            fat = conv(add.fat_concentration, add.fat_concentration_unit, volume)
            glc = 0.0
            return {'Na':na, 'K':k, 'Cl':cl, 'Ca':ca, 'Mg':mg, 'Zn':zn, 'P':p, 'Amino Acids':amino,'Fats':fat,'Glucose':glc}

        def get_special_glucose(percentage_str, volume):
            # 50%ブドウ糖液: 0.5 g/mL
            val = 0.5
            return {'Na':0, 'K':0, 'Cl':0, 'Ca':0, 'Mg':0, 'Zn':0, 'P':0, 'Amino Acids':0, 'Fats':0, 'Glucose':val * volume}

        def get_dist_nutrients(additive_name, volume, solutions, additives):
            if additive_name.startswith("ベース製剤（"):
                sol_name = additive_name.replace("ベース製剤（","").replace("）","")
                sol = next((s for s in solutions if s.name == sol_name), None)
                return get_solution_nutrients(sol, volume)
            elif additive_name in additives:
                return get_additive_nutrients(additives[additive_name], volume)
            elif additive_name == "50%ブドウ糖液":
                return get_special_glucose("50%", volume)
            elif additive_name == "蒸留水":
                return {c:0.0 for c in components}
            else:
                return {c:0.0 for c in components}

        table_data = []
        total_components_dict = {c:0.0 for c in components}

        for additive_name, vol in infusion_mix.detailed_mix.items():
            row = [additive_name, f"{vol:.2f}"]
            nut = get_dist_nutrients(additive_name, vol, solutions, additives)
            for c in components:
                val = nut[c]
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

        with st.expander("詳細計算ステップを表示"):
            steps_formatted = infusion_mix.calculation_steps.replace("\n", "\n")
            st.markdown(f"**計算ステップ:**\n\n{steps_formatted}")

if __name__ == "__main__":
    main()
