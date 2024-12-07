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

# ログの設定
setup_logging()
logging.info("アプリケーションの起動")

# ページの設定
st.set_page_config(
    page_title="TPN 配合計算アプリケーション",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSSの適用（オプション）
st.markdown(
    """
    <style>
    .main {
        background-color: #F0F2F6;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
    }
    .warning {
        color: #FF0000;
    }
    </style>
    """,
    unsafe_allow_html=True
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
        'weight': 70.0,
        'twi': 110.0,
        'selected_solution': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_values():
    # 必要なキーのみ初期化
    keys_to_keep = {
        'gir_checkbox', 'gir_input', 'amino_acid_checkbox', 'amino_acid_input',
        'na_checkbox', 'na_input', 'k_checkbox', 'k_input', 'cl_checkbox', 'cl_input',
        'ca_checkbox', 'ca_input', 'mg_checkbox', 'mg_input', 'zn_checkbox', 'zn_input',
        'weight', 'twi', 'selected_solution'
    }
    for k in list(st.session_state.keys()):
        if k not in keys_to_keep:
            del st.session_state[k]
    # 初期値を再設定
    initialize_session_state()
    st.experimental_rerun()

def create_patient_object(weight, twi,
                          gir_included, gir,
                          amino_acid_included, amino_acid,
                          na_included, na,
                          k_included, k,
                          cl_included, cl,
                          ca_included, ca,
                          mg_included, mg,
                          zn_included, zn):
    # P, fat は現状Noneにしているが、必要ならフォームを追加し対応
    patient = Patient(
        weight=weight,
        twi=twi,
        gir=gir if gir_included else None,
        gir_included=gir_included,
        amino_acid=amino_acid if amino_acid_included else None,
        amino_acid_included=amino_acid_included,
        na=na if na_included else None,
        na_included=na_included,
        k=k if k_included else None,
        k_included=k_included,
        p=None,
        p_included=False,
        fat=None,
        fat_included=False,
        ca=ca if ca_included else None,
        ca_included=ca_included,
        mg=mg if mg_included else None,
        mg_included=mg_included,
        zn=zn if zn_included else None,
        zn_included=zn_included,
        cl=cl if cl_included else None,
        cl_included=cl_included
    )
    return patient

def main():
    initialize_session_state()
    
    # アプリ概要説明
    st.title("TPN 配合計算アプリケーション")
    st.markdown("""
    このアプリは、患者情報（体重、TWIなど）および栄養素要求量（GIR、電解質など）に基づき、TPN（中心静脈栄養）の配合を計算するツールです。
    
    **使い方：**
    1. **輸液製剤の選択**: 下でベース製剤を選びます。
    2. **患者情報の入力**: 2列フォームで体重やTWI、電解質要求量を入力します。
    3. **配合計算**: 「配合を計算」ボタンを押すと結果が表示されます。
    4. **結果の確認**: 目標値との差分が表示され、再調整が必要かどうかを確認できます。
    
    **注意：**
    これはデモ用であり、実際の医療行為には使用しないでください。
    """)

    st.markdown("---")
    st.header("輸液製剤の選択")
    
    # ベース製剤と添加剤のロード
    solutions = load_solutions()
    additives = load_additives()
    
    if not solutions or not additives:
        st.error("データのロードに失敗しました。ファイルやデータを確認してください。")
        st.stop()
    
    # ベース製剤の選択
    selected_solution_name = st.selectbox(
        "ベース製剤を選択してください",
        [sol.name for sol in solutions],
        key="base_solution_selectbox"
    )
    selected_solution = next((sol for sol in solutions if sol.name == selected_solution_name), None)
    # selected_solutionをsession_stateに保存
    st.session_state['selected_solution'] = selected_solution
    
    # 選択されたベース製剤の組成をリアルタイムで表示
    if selected_solution:
        st.markdown("**選択されたベース製剤の組成:**")
        sol_df = pd.DataFrame({
            "項目": [
                f"ブドウ糖濃度 ({selected_solution.glucose_unit})",
                f"Na⁺ ({selected_solution.na_unit})",
                f"K⁺ ({selected_solution.k_unit})",
                f"Cl⁻ ({selected_solution.cl_unit})",
                f"P ({selected_solution.p_unit})",
                f"カロリー ({selected_solution.calories_unit})",
                f"Mg²⁺ ({selected_solution.mg_unit})",
                f"Ca²⁺ ({selected_solution.ca_unit})",
                f"Zn ({selected_solution.zn_unit})"
            ],
            "値": [
                f"{selected_solution.glucose_percentage} {selected_solution.glucose_unit}",
                f"{selected_solution.na} {selected_solution.na_unit}",
                f"{selected_solution.k} {selected_solution.k_unit}",
                f"{selected_solution.cl} {selected_solution.cl_unit}",
                f"{selected_solution.p} {selected_solution.p_unit}",
                f"{selected_solution.calories} {selected_solution.calories_unit}",
                f"{selected_solution.mg} {selected_solution.mg_unit}",
                f"{selected_solution.ca} {selected_solution.ca_unit}",
                f"{selected_solution.zn} {selected_solution.zn_unit}"
            ]
        })
        st.table(sol_df)
    
    st.markdown("---")
    st.header("患者情報の入力")
    
    # 患者情報の入力フォームを2列に整理
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本情報")
        weight = st.number_input(
            "体重 (kg)",
            min_value=0.1,
            max_value=150.0,
            key="weight",
            step=0.01,
            format="%.2f",
            help="患者の体重をkg単位で入力してください。通常は1~150kg程度。"
        )
        if weight < 2.0 or weight > 120.0:
            st.warning("体重が通常範囲外です。値を再確認してください。")
    
        twi = st.number_input(
            "TWI (mL/kg/day)",
            min_value=50.0,
            max_value=200.0,
            step=1.0,
            key="twi",
            help="総投与量 (TWI) をmL/kg/day単位で入力してください。通常100~150mL/kg/day程度。"
        )
        if twi < 70 or twi > 150:
            st.warning("TWIが一般的な範囲外です。異常な値でないか確認してください。")
    
        gir_included = st.checkbox("GIRを条件に含める", key="gir_checkbox")
        gir = st.number_input(
            "GIR (mg/kg/min)",
            min_value=4.0,
            max_value=10.0,
            disabled=not gir_included,
            key="gir_input",
            step=0.1,
            help="GIRをmg/kg/min単位で入力してください。通常4~8 mg/kg/min程度から開始。"
        )
    
        amino_acid_included = st.checkbox("アミノ酸量を条件に含める", key="amino_acid_checkbox")
        amino_acid = st.number_input(
            "アミノ酸量 (g/kg/day)",
            min_value=2.0,
            max_value=4.0,
            step=0.1,
            disabled=not amino_acid_included,
            key="amino_acid_input",
            help="アミノ酸量をg/kg/dayで入力。2~3 g/kg/day程度が目安。"
        )
    
    with col2:
        st.subheader("電解質 & ミネラル")
        na_included = st.checkbox("Na量を条件に含める", key="na_checkbox")
        na = st.number_input(
            "Na量 (mEq/kg/day)",
            min_value=2.0,
            max_value=4.0,
            step=0.1,
            disabled=not na_included,
            key="na_input",
            help="Na量をmEq/kg/dayで入力。2~3 mEq/kg/day程度が一般的。"
        )
    
        k_included = st.checkbox("K量を条件に含める", key="k_checkbox")
        k = st.number_input(
            "K量 (mEq/kg/day)",
            min_value=1.0,
            max_value=3.0,
            step=0.1,
            disabled=not k_included,
            key="k_input",
            help="K量をmEq/kg/dayで入力。1~2 mEq/kg/day程度を目安。"
        )
    
        cl_included = st.checkbox("Cl量を条件に含める", key="cl_checkbox")
        cl = st.number_input(
            "Cl量 (mEq/kg/day)",
            min_value=0.0,
            max_value=5.0,
            step=0.1,
            disabled=not cl_included,
            key="cl_input",
            help="Cl量をmEq/kg/dayで入力。0~3程度が一般的。"
        )
    
        ca_included = st.checkbox("Ca量を条件に含める", key="ca_checkbox")
        ca = st.number_input(
            "Ca量 (mEq/kg/day)",
            min_value=0.0,
            max_value=5.0,
            step=0.1,
            disabled=not ca_included,
            key="ca_input",
            help="Ca量をmEq/kg/dayで入力。0.5~1 mEq/kg/day程度が目安。"
        )
    
        mg_included = st.checkbox("Mg量を条件に含める", key="mg_checkbox")
        mg = st.number_input(
            "Mg量 (mEq/kg/day)",
            min_value=0.0,
            max_value=5.0,
            step=0.1,
            disabled=not mg_included,
            key="mg_input",
            help="Mg量をmEq/kg/dayで入力。0.1~0.3 mEq/kg/day程度が目安。"
        )
    
        zn_included = st.checkbox("Zn量を条件に含める", key="zn_checkbox")
        zn = st.number_input(
            "Zn量 (mmol/kg/day)",
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            disabled=not zn_included,
            key="zn_input",
            help="Zn量をmmol/kg/dayで入力。0.05~0.1 mmol/kg/day程度が一般的。"
        )
    
    st.markdown("---")
    button_cols = st.columns([1, 1, 4])
    with button_cols[0]:
        if st.button('リセット', type="secondary", use_container_width=True):
            reset_values()
    
    with button_cols[1]:
        calculate_button = st.button('配合を計算', type="primary", use_container_width=True)
    
    # ボタンのスタイル調整
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        font-weight: bold;
        padding: 0.5rem 1rem;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 計算ボタンの処理
    if calculate_button:
        with st.spinner('計算中...'):
            try:
                # session_stateからselected_solutionを取得
                current_solution = st.session_state.get('selected_solution', None)
                if current_solution is None:
                    st.error("ベース製剤が選択されていません。上部で製剤を選択してください。")
                    raise ValueError("selected_solution is None")
    
                # Patientオブジェクトの作成（関数化済み）
                patient = create_patient_object(
                    weight=st.session_state.weight,
                    twi=st.session_state.twi,
                    gir_included=st.session_state.gir_checkbox,
                    gir=st.session_state.gir_input,
                    amino_acid_included=st.session_state.amino_acid_checkbox,
                    amino_acid=st.session_state.amino_acid_input,
                    na_included=st.session_state.na_checkbox,
                    na=st.session_state.na_input,
                    k_included=st.session_state.k_checkbox,
                    k=st.session_state.k_input,
                    cl_included=st.session_state.cl_checkbox,
                    cl=st.session_state.cl_input,
                    ca_included=st.session_state.ca_checkbox,
                    ca=st.session_state.ca_input,
                    mg_included=st.session_state.mg_checkbox,
                    mg=st.session_state.mg_input,
                    zn_included=st.session_state.zn_checkbox,
                    zn=st.session_state.zn_input
                )
                
                logging.debug(f"患者データ: {patient}")
                logging.debug(f"選択されたベース製剤: {current_solution}")
    
                # 計算の実行
                infusion_mix = calculate_infusion(patient, current_solution, additives)
                logging.debug(f"計算結果: {infusion_mix}")
    
                # 計算結果をセッションステートに保存
                st.session_state['infusion_mix'] = infusion_mix
    
            except ValidationError as e:
                st.error("入力値に誤りがあります。再度確認してください。")
                logging.error(f"ValidationError: {e}")
            except ValueError as ve:
                st.error(str(ve))
                logging.error(f"ValueError: {ve}")
            except Exception as e:
                st.error("計算中にエラーが発生しました。詳細はログを確認してください。")
                logging.error(f"Unexpected error: {e}")
    
    # 計算結果の表示
    if 'infusion_mix' in st.session_state and st.session_state['infusion_mix'] is not None:
        infusion_mix = st.session_state['infusion_mix']
        current_solution = st.session_state.get('selected_solution', None)
        if current_solution is None:
            st.error("ベース製剤情報が見つかりません。再度計算してください。")
            st.stop()
        
        # 再度Patient作成（結果確認用）※本来はpatientもsession_stateに保持するのが望ましい
        patient = create_patient_object(
            weight=st.session_state.weight,
            twi=st.session_state.twi,
            gir_included=st.session_state.gir_checkbox,
            gir=st.session_state.gir_input,
            amino_acid_included=st.session_state.amino_acid_checkbox,
            amino_acid=st.session_state.amino_acid_input,
            na_included=st.session_state.na_checkbox,
            na=st.session_state.na_input,
            k_included=st.session_state.k_checkbox,
            k=st.session_state.k_input,
            cl_included=st.session_state.cl_checkbox,
            cl=st.session_state.cl_input,
            ca_included=st.session_state.ca_checkbox,
            ca=st.session_state.ca_input,
            mg_included=st.session_state.mg_checkbox,
            mg=st.session_state.mg_input,
            zn_included=st.session_state.zn_checkbox,
            zn=st.session_state.zn_input
        )
    
        st.markdown("---")
        st.header("計算結果")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("基本情報")
            # 入力値と結果を比較して差分をメトリックで表示
            def show_metric(label, input_val, unit, result_val):
                if input_val is not None and result_val is not None:
                    diff = result_val - input_val
                    st.metric(label, f"{result_val:.2f} {unit}", f"{diff:.2f}")
            
            if infusion_mix.gir is not None and st.session_state.gir_checkbox:
                show_metric("GIR (mg/kg/min)", st.session_state.gir_input, "mg/kg/min", infusion_mix.gir)
            if infusion_mix.amino_acid is not None and st.session_state.amino_acid_checkbox:
                show_metric("アミノ酸量 (g/kg/day)", st.session_state.amino_acid_input, "g/kg/day", infusion_mix.amino_acid)
            if infusion_mix.na is not None and st.session_state.na_checkbox:
                show_metric("Na量 (mEq/kg/day)", st.session_state.na_input, "mEq/kg/day", infusion_mix.na)
            if infusion_mix.k is not None and st.session_state.k_checkbox:
                show_metric("K量 (mEq/kg/day)", st.session_state.k_input, "mEq/kg/day", infusion_mix.k)
            if infusion_mix.cl is not None and st.session_state.cl_checkbox:
                show_metric("Cl量 (mEq/kg/day)", st.session_state.cl_input, "mEq/kg/day", infusion_mix.cl)
            if infusion_mix.ca is not None and st.session_state.ca_checkbox:
                show_metric("Ca量 (mEq/kg/day)", st.session_state.ca_input, "mEq/kg/day", infusion_mix.ca)
            if infusion_mix.mg is not None and st.session_state.mg_checkbox:
                show_metric("Mg量 (mEq/kg/day)", st.session_state.mg_input, "mEq/kg/day", infusion_mix.mg)
            if infusion_mix.zn is not None and st.session_state.zn_checkbox:
                show_metric("Zn量 (mmol/kg/day)", st.session_state.zn_input, "mmol/kg/day", infusion_mix.zn)
    
        with col2:
            st.subheader("その他の情報")
            st.write(f"**総投与量 (TWI):** {patient.twi * patient.weight:.2f} mL/day")
            # 総液量がTWIに近いかどうかチェック
            total_volume = sum(infusion_mix.detailed_mix.values())
            diff_twi = total_volume - (patient.twi * patient.weight)
            st.metric("最終総液量 (mL/day)", f"{total_volume:.2f} mL/day", f"{diff_twi:.2f} mL/day")
            if abs(diff_twi) > 50:
                st.warning("最終総液量が目標TWIから大きく外れています。パラメータを見直してください。")
        
        # 混合溶液の詳細
        st.subheader("混合溶液の詳細")
        df = {
            "製剤名": list(infusion_mix.detailed_mix.keys()),
            "必要量 (mL/day)": [f"{value:.2f}" for value in infusion_mix.detailed_mix.values()]
        }
        st.table(df)
        
        # 計算ステップの詳細
        st.subheader("計算ステップの詳細")
        with st.expander("計算ステップを表示"):
            steps_formatted = infusion_mix.calculation_steps.replace("\n", "\n")
            st.markdown(f"**計算ステップ:**\n\n{steps_formatted}")
            st.info("各計算ステップを確認してください。")
    
        # 最終的な混合溶液中の各栄養素の量（参考）
        st.subheader("最終的な混合溶液中の各栄養素の量（参考）")
        final_mix = infusion_mix.nutrient_totals
        nutrient_units = infusion_mix.nutrient_units
        input_amounts = infusion_mix.input_amounts
        input_units = infusion_mix.input_units
        nutrient_per_kg = {nutrient: total / patient.weight for nutrient, total in final_mix.items()}
        
        nutrient_df = pd.DataFrame({
            "栄養素": list(nutrient_units.keys()),
            "入力量": [f"{input_amounts.get(n, 0.0):.2f}" for n in nutrient_units.keys()],
            "入力単位": [input_units.get(n, "") for n in nutrient_units.keys()],
            "最終溶液中の量": [f"{final_mix.get(n, 0.0):.2f}" for n in nutrient_units.keys()],
            "最終溶液中の量単位": [nutrient_units.get(n, "") for n in nutrient_units.keys()],
            "最終溶液中の量 (kg単位)": [f"{nutrient_per_kg.get(n, 0.0):.2f}" for n in nutrient_units.keys()],
            "最終溶液中の量 (kg単位) 単位": [nutrient_units.get(n, "").replace("/day", "/day/kg") for n in nutrient_units.keys()]
        })
        st.table(nutrient_df)

if __name__ == "__main__":
    main()
