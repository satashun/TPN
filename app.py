# app.py
import streamlit as st
import json
from models import Patient, Solution, InfusionMix
from calculation import calculate_infusion
from pydantic import ValidationError
import logging
import os

# ユーティリティ関数をインポート
from utils import setup_logging

# ログの設定
setup_logging()

# ログ出力
logger = logging.getLogger()

# 輸液製剤のデータをロード
def load_solutions(file_path='data/solutions.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            solutions_data = json.load(f)
        solutions = [Solution(**sol) for sol in solutions_data]
        logger.debug("製剤データのロードに成功しました。")
        return solutions
    except FileNotFoundError:
        logger.error(f"製剤データファイルが見つかりません: {file_path}")
        st.error(f"製剤データファイルが見つかりません: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"製剤データファイルのJSON解析エラー: {e}")
        st.error(f"製剤データファイルのJSON解析エラー: {e}")
        return []

# Streamlit Appのメイン関数
def main():
    st.title("TPN 配合計算アプリケーション")
    
    # 輸液製剤のロード
    solutions = load_solutions()
    
    if not solutions:
        st.stop()  # 製剤データがロードできない場合、アプリを停止
    
    st.header("患者情報の入力")
    with st.form(key='patient_form'):
        weight = st.number_input("体重 (kg)", min_value=0.1, max_value=10.0, value=1.33, step=0.01)
        twi = st.number_input("TWI (mL/kg/day)", min_value=50.0, max_value=200.0, value=110.0, step=1.0)
        gir = st.number_input("GIR (mg/kg/min)", min_value=4.0, max_value=10.0, value=7.0, step=0.1)
        amino_acid = st.number_input("アミノ酸量 (g/kg/day)", min_value=2.0, max_value=4.0, value=3.0, step=0.1)
        na = st.number_input("Na量 (mEq/kg/day)", min_value=2.0, max_value=4.0, value=2.5, step=0.1)
        k = st.number_input("K量 (mEq/kg/day)", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
        p = st.number_input("P量 (mmol/kg/day)", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
        
        submit_button = st.form_submit_button(label='計算する')
    
    if submit_button:
        try:
            # Patientオブジェクトの作成
            patient = Patient(
                weight=weight,
                twi=twi,
                gir=gir,
                amino_acid=amino_acid,
                na=na,
                k=k,
                p=p
            )
            logger.debug(f"患者データ: {patient}")
        except ValidationError as e:
            st.error("入力値に誤りがあります。再度確認してください。")
            logger.error(f"ValidationError: {e}")
            return
        
        st.header("輸液製剤の選択")
        selected_solution_name = st.selectbox("ベース製剤を選択してください", [sol.name for sol in solutions])
        selected_solution = next((sol for sol in solutions if sol.name == selected_solution_name), None)
        logger.debug(f"選択された製剤: {selected_solution}")
        
        if st.button("配合を計算"):
            try:
                infusion_mix = calculate_infusion(patient, selected_solution)
                logger.debug(f"計算結果: {infusion_mix}")
                
                st.subheader("計算結果")
                st.write(f"GIR: {infusion_mix.gir:.2f} mg/kg/min")
                st.write(f"アミノ酸量: {infusion_mix.amino_acid:.2f} g/kg/day")
                st.write(f"Na量: {infusion_mix.na:.2f} mEq/kg/day")
                st.write(f"K量: {infusion_mix.k:.2f} mEq/kg/day")
                st.write(f"P量: {infusion_mix.p:.2f} mmol/kg/day")
                
                st.subheader("混合溶液の詳細")
                for key, value in infusion_mix.detailed_mix.items():
                    st.write(f"{key}: {value:.2f} mL/day")
            except ValueError as ve:
                st.error(str(ve))
                logger.error(f"ValueError: {ve}")
            except Exception as e:
                st.error("計算中にエラーが発生しました。詳細はログを確認してください。")
                logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
